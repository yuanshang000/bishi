"""
RAG服务

提供文档向量化和检索增强生成功能
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import hashlib
import logging
import yaml
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import CourseDocument

logger = logging.getLogger(__name__)


class RAGService:
    """RAG服务类"""

    def __init__(self):
        """初始化RAG服务"""
        # 加载配置
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        # 获取文档处理配置
        self.doc_config = self.config.get("document_processing", {})
        self.chunk_size = self.doc_config.get("chunk_size", 800)
        self.chunk_overlap = self.doc_config.get("chunk_overlap", 100)

        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"description": "College English course documents"}
        )

        # 初始化Embedding客户端
        self.embed_client = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )

        self.embed_model = settings.EMBEDDING_MODEL

        logger.info(f"RAG Service initialized with collection: {settings.CHROMA_COLLECTION_NAME}")

    def split_text(self, text: str) -> List[str]:
        """
        改进的文本分块策略

        优化目标：
        1. 保持教学内容的完整性（如一个知识点的所有内容在一起）
        2. 避免产生过多的小块
        3. 优先按大段落分割，而不是小段落

        Args:
            text: 原始文本

        Returns:
            List[str]: 文本块列表
        """
        import re

        # 先按大的分割点分割（如章节标题）
        # 匹配类似"章节四："、"1. "、"2. "等大标题
        major_sections = re.split(r'\n(?=[章节第]\w+[：:、.]|\d+\.\s+[^\d])', text)

        chunks = []
        current_chunk = ""

        for section in major_sections:
            section = section.strip()
            if not section:
                continue

            # 如果这个section本身就很大，需要进一步分割
            if len(section) > self.chunk_size * 1.5:
                # 按小标题分割
                sub_sections = re.split(r'\n(?=\d+\.\d+\s+)', section)

                for sub_section in sub_sections:
                    sub_section = sub_section.strip()
                    if not sub_section:
                        continue

                    # 如果当前块+新小节超过限制
                    if len(current_chunk) + len(sub_section) > self.chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sub_section
                    else:
                        if current_chunk:
                            current_chunk += "\n\n" + sub_section
                        else:
                            current_chunk = sub_section
            else:
                # section不大，直接处理
                if len(current_chunk) + len(section) > self.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = section
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + section
                    else:
                        current_chunk = section

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        # 如果最终只产生了1个chunk且长度合理，那很好
        # 如果产生了很多小chunks（每个都很短），尝试合并它们
        if len(chunks) > 1:
            merged_chunks = []
            current_merged = ""

            for chunk in chunks:
                # 如果chunk太短（小于200字符），尝试与前面的合并
                if len(chunk) < 200:
                    if current_merged:
                        current_merged += "\n\n" + chunk
                    else:
                        current_merged = chunk
                else:
                    # chunk足够大
                    if current_merged:
                        # 检查合并后的长度
                        if len(current_merged) + len(chunk) <= self.chunk_size:
                            current_merged += "\n\n" + chunk
                        else:
                            # 先保存当前合并的
                            merged_chunks.append(current_merged.strip())
                            current_merged = chunk
                    else:
                        current_merged = chunk

            # 添加最后一个合并的chunk
            if current_merged:
                merged_chunks.append(current_merged.strip())

            # 如果合并后的chunks数量更合理，使用合并后的
            if len(merged_chunks) < len(chunks):
                chunks = merged_chunks
                logger.info(f"Merged small chunks: {len(chunks)} final chunks")

        logger.info(f"Split text into {len(chunks)} chunks (sizes: {[len(c) for c in chunks]})")
        return chunks

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        获取文本向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        try:
            response = self.embed_client.embeddings.create(
                model=self.embed_model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def vectorize_document(
        self,
        db: Session,
        document_id: int
    ) -> bool:
        """
        向量化文档

        Args:
            db: 数据库会话
            document_id: 文档ID

        Returns:
            bool: 成功返回True
        """
        try:
            # 获取文档
            doc = db.query(CourseDocument).filter(CourseDocument.id == document_id).first()
            if not doc or not doc.content:
                logger.warning(f"Document {document_id} not found or has no content")
                return False

            # 检查是否已向量化
            if doc.is_vectorized:
                logger.info(f"Document {document_id} already vectorized")
                return True

            # 🔥 清理文档内容（标记提取或传统清理）
            from app.api.v1.documents import clean_document_properties
            cleaned_content = clean_document_properties(doc.content)

            if not cleaned_content or len(cleaned_content.strip()) < 50:
                logger.error(f"Document {document_id} content too short after cleaning: {len(cleaned_content)} chars")
                return False

            logger.info(f"Document {document_id} cleaned: {len(doc.content)} -> {len(cleaned_content)} chars")

            # 分块（使用清理后的内容）
            chunks = self.split_text(cleaned_content)
            if not chunks:
                logger.warning(f"No chunks generated for document {document_id}")
                return False

            # 生成向量
            embeddings = self.get_embeddings(chunks)

            # 生成唯一ID
            chunk_ids = [
                f"doc_{doc.id}_chunk_{i}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                for i, chunk in enumerate(chunks)
            ]

            # 准备元数据 - 确保所有值都是正确的类型
            metadatas = [
                {
                    "document_id": int(doc.id),
                    "chapter_id": int(doc.chapter_id),  # 确保是整数
                    "doc_type": str(doc.doc_type.value),
                    "title": str(doc.title),
                    "chunk_index": int(i),
                }
                for i in range(len(chunks))
            ]

            logger.info(f"Vectorizing document: doc_id={doc.id}, chapter_id={doc.chapter_id}, title='{doc.title}', chunks={len(chunks)}")

            # 批量添加到ChromaDB
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                end_idx = min(i + batch_size, len(chunks))
                self.collection.add(
                    ids=chunk_ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=chunks[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )

            # 更新数据库记录
            doc.is_vectorized = 1
            doc.vector_count = len(chunks)
            import json
            doc.chroma_ids = json.dumps(chunk_ids)

            db.commit()

            logger.info(f"Document {document_id} vectorized: {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error vectorizing document {document_id}: {e}")
            db.rollback()
            return False

    def vectorize_text(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        通用文本向量化
        
        Args:
            text: 要向量化的文本
            metadata: 元数据 (必须包含 'source_id', 'source_type')
            
        Returns:
            bool: 成功返回True
        """
        try:
            if not text or len(text.strip()) < 10:
                logger.warning("Text too short to vectorize")
                return False

            # 分块
            chunks = self.split_text(text)
            if not chunks:
                logger.warning("No chunks generated from text")
                return False

            # 生成向量
            embeddings = self.get_embeddings(chunks)
            
            source_id = metadata.get('source_id')
            source_type = metadata.get('source_type', 'unknown')
            
            # 生成唯一ID
            chunk_ids = [
                f"{source_type}_{source_id}_chunk_{i}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                for i, chunk in enumerate(chunks)
            ]

            # 准备元数据
            metadatas = []
            for i in range(len(chunks)):
                meta = metadata.copy()
                meta['chunk_index'] = i
                # Ensure all values are strings, ints, floats, or bools
                for k, v in meta.items():
                    if v is None:
                        meta[k] = ""
                    elif not isinstance(v, (str, int, float, bool)):
                        meta[k] = str(v)
                metadatas.append(meta)

            logger.info(f"Vectorizing {source_type} {source_id}: {len(chunks)} chunks")

            # 批量添加到ChromaDB
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                end_idx = min(i + batch_size, len(chunks))
                self.collection.add(
                    ids=chunk_ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=chunks[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Error vectorizing text: {e}")
            return False

    def vectorize_subsection(
        self,
        db: Session,
        subsection_id: int
    ) -> bool:
        """
        向量化小目标内容
        """
        try:
            from app.models.subsection import SubSection
            from app.models.section import Section
            from app.models.chapter import Chapter
            
            subsection = db.query(SubSection).filter(SubSection.id == subsection_id).first()
            if not subsection or not subsection.content:
                logger.warning(f"SubSection {subsection_id} not found or empty")
                return False
                
            # 获取上下文信息
            section = db.query(Section).filter(Section.id == subsection.section_id).first()
            chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first() if section else None
            
            # 清除旧向量
            self.delete_source_vectors(source_id=subsection_id, source_type="subsection")
            
            # 准备元数据
            metadata = {
                "source_id": subsection_id,
                "source_type": "subsection",
                "title": subsection.title,
                "section_title": section.title if section else "",
                "chapter_title": chapter.title if chapter else "",
                "chapter_id": chapter.id if chapter else 0,
                "section_id": section.id if section else 0,
                "subsection_id": subsection_id
            }
            
            return self.vectorize_text(subsection.content, metadata)
            
        except Exception as e:
            logger.error(f"Error vectorizing subsection {subsection_id}: {e}")
            return False

    def delete_source_vectors(self, source_id: int, source_type: str) -> bool:
        """删除指定来源的向量"""
        try:
            self.collection.delete(
                where={
                    "$and": [
                        {"source_id": int(source_id)},  # Make sure it matches how we stored it (int vs str?)
                        # Chroma where clause implies equality. 
                        # Ideally we stored source_id as int in metadata if possible, 
                        # but in vectorize_text we might have converted to str if it wasn't int.
                        # Let's check vectorize_text: we pass it as is, but then loop ensures simple types.
                        # If passed as int, it stays int.
                        {"source_type": source_type}
                    ]
                }
            )
            # Try simple delete if $and fails or if we used different keys
            # Actually, let's just use source_id and source_type if they are in metadata
            # In vectorize_text, we put source_id in metadata.
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors for {source_type} {source_id}: {e}")
            return False

    def delete_chapter_vectors(self, chapter_id: int) -> bool:
        """删除指定章节的所有向量"""
        try:
            # We store chapter_id in metadata for subsections
            self.collection.delete(
                where={"chapter_id": int(chapter_id)}
            )
            logger.info(f"Deleted vectors for chapter {chapter_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors for chapter {chapter_id}: {e}")
            return False

    def search(
        self,
        query: str,
        chapter_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 查询文本
            chapter_id: 章节ID（可选，用于过滤）
            top_k: 返回结果数量

        Returns:
            List[Dict]: 检索结果列表
        """
        try:
            # 生成查询向量
            query_embedding = self.get_embeddings([query])[0]

            # 构建过滤条件 - 确保类型一致
            where = {}
            if chapter_id is not None:
                where["chapter_id"] = int(chapter_id)  # 确保是整数
                logger.info(f"Filtering by chapter_id: {chapter_id} (type: {type(chapter_id).__name__})")

            logger.info(f"Searching with query: '{query[:50]}...', chapter_id: {chapter_id}, top_k: {top_k}, where: {where}")

            # 检索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where if where else None,
                include=["documents", "metadatas", "distances"]
            )

            # 格式化结果
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "score": 1 - results['distances'][0][i] if results['distances'] else 0,  # 转换为相似度分数
                    })

                    # 详细日志：记录每个检索到的文档
                    logger.info(f"  - Retrieved chunk {i+1}: doc_id={metadata.get('document_id')}, "
                              f"chapter_id={metadata.get('chapter_id')}, "  # 添加章节ID到日志
                              f"title='{metadata.get('title', 'N/A')}', "
                              f"doc_type={metadata.get('doc_type')}, "
                              f"score={1 - results['distances'][0][i]:.4f}, "
                              f"content_preview='{doc[:50]}...'")
            else:
                logger.warning(f"No results found for chapter_id={chapter_id}, query='{query[:50]}...'")

            logger.info(f"Retrieved {len(formatted_results)} results total")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def delete_document_vectors(self, document_id: int) -> bool:
        """
        删除文档的向量

        Args:
            document_id: 文档ID

        Returns:
            bool: 成功返回True
        """
        try:
            # 查找该文档的所有向量ID - 确保类型一致
            results = self.collection.get(
                where={"document_id": int(document_id)}  # 确保是整数
            )

            if results and results['ids']:
                logger.info(f"Found {len(results['ids'])} vectors for document {document_id}, deleting...")
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} vectors for document {document_id}")

                # 强制持久化，确保删除操作立即生效
                try:
                    self.chroma_client.persist()
                    logger.info(f"Persisted deletion of vectors for document {document_id}")
                except Exception as persist_error:
                    logger.warning(f"Failed to persist after deletion: {persist_error}")

                return True

            logger.warning(f"No vectors found for document {document_id}")
            return False

        except Exception as e:
            logger.error(f"Error deleting vectors for document {document_id}: {e}")
            return False

    def get_context_for_query(
        self,
        query: str,
        chapter_id: Optional[int] = None,
        max_length: int = 2000
    ) -> tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        为查询获取上下文

        Args:
            query: 查询文本
            chapter_id: 章节ID
            max_length: 最大上下文长度

        Returns:
            tuple: (上下文文本, 使用的文档元数据列表)
        """
        results = self.search(query, chapter_id=chapter_id, top_k=5)

        if not results:
            logger.warning("No search results found for context")
            return "", [], []

        # 拼接上下文，控制长度
        context_parts = []
        current_length = 0
        used_documents = []
        used_chunks = []

        for result in results:
            content = result['content']
            metadata = result['metadata']

            if current_length + len(content) > max_length:
                # 截断最后一部分
                remaining = max_length - current_length
                if remaining > 100:  # 至少保留100字符
                    context_parts.append(content[:remaining] + "...")
                break

            context_parts.append(content)
            current_length += len(content)

            # 收集文档信息（去重）
            doc_info = {
                "document_id": metadata.get('document_id'),
                "title": metadata.get('title'),
                "doc_type": metadata.get('doc_type')
            }
            if doc_info not in used_documents:
                used_documents.append(doc_info)
            
            chunk_preview = {
                "index": len(used_chunks),
                "length": len(content),
                "preview": content[:200] + ("..." if len(content) > 200 else ""),
                "document_id": metadata.get('document_id'),
                "title": metadata.get('title'),
                "doc_type": metadata.get('doc_type'),
                "score": result.get('score', 0)
            }
            used_chunks.append(chunk_preview)

        logger.info(f"Context built from {len(used_documents)} documents, total length: {current_length} chars")
        for doc in used_documents:
            logger.info(f"  - Using document: {doc}")

        return "\n\n---\n\n".join(context_parts), used_documents, used_chunks

    def get_context_for_subsection(
        self,
        subsection_id: int,
        max_length: int = 2000,
        top_k: int = 5
    ) -> tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        为指定小目标获取上下文（仅使用该小目标的向量化内容）

        Args:
            subsection_id: 小目标ID
            max_length: 最大上下文长度
            top_k: 检索的分块数量

        Returns:
            tuple: (上下文文本, 使用的文档元数据列表, 使用的分块预览列表)
        """
        try:
            # 使用小目标标题作为查询文本以提高相关性
            from app.models.subsection import SubSection
            from app.core.database import SessionLocal
            tmp_db = None
            subsection_title = ""
            try:
                tmp_db = SessionLocal()
                sub = tmp_db.query(SubSection).filter(SubSection.id == subsection_id).first()
                subsection_title = (sub.title if sub else f"Subsection {subsection_id}") or f"Subsection {subsection_id}"
            except Exception:
                subsection_title = f"Subsection {subsection_id}"
            finally:
                if tmp_db:
                    tmp_db.close()

            query_embedding = self.get_embeddings([subsection_title])[0]

            # 仅检索该小目标的向量
            where = {
                "subsection_id": int(subsection_id),
                "source_type": "subsection"
            }
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            if not results or not results.get('documents'):
                logger.warning(f"No vectors found for subsection {subsection_id}")
                return "", [], []

            context_parts: List[str] = []
            current_length = 0
            used_documents: List[Dict[str, Any]] = []
            used_chunks: List[Dict[str, Any]] = []

            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                score = 1 - results['distances'][0][i] if results.get('distances') else 0

                if current_length + len(doc) > max_length:
                    remaining = max_length - current_length
                    if remaining > 100:
                        context_parts.append(doc[:remaining] + "...")
                    break

                context_parts.append(doc)
                current_length += len(doc)

                used_chunks.append({
                    "index": metadata.get('chunk_index', 0),
                    "length": len(doc),
                    "preview": doc[:200] + ("..." if len(doc) > 200 else ""),
                    "document_id": None,
                    "title": metadata.get('title'),
                    "doc_type": "subsection",
                    "section_title": metadata.get('section_title'),
                    "chapter_title": metadata.get('chapter_title'),
                    "subsection_id": metadata.get('subsection_id'),
                    "score": score
                })

            context_text = "\n\n".join(context_parts)
            return context_text, used_documents, used_chunks
        except Exception as e:
            logger.error(f"Error getting context for subsection {subsection_id}: {e}")
            return "", [], []

    def clear_all_vectors(self) -> int:
        """
        清空整个向量集合

        Returns:
            int: 删除的向量数量
        """
        try:
            # 获取所有向量
            all_data = self.collection.get()
            total_count = len(all_data['ids']) if all_data['ids'] else 0

            if total_count > 0:
                # 删除所有向量
                self.collection.delete(ids=all_data['ids'])
                logger.info(f"Cleared all {total_count} vectors from collection")

                # 强制持久化
                try:
                    self.chroma_client.persist()
                    logger.info(f"Persisted after clearing all vectors")
                except Exception as persist_error:
                    logger.warning(f"Failed to persist after clearing: {persist_error}")

            return total_count

        except Exception as e:
            logger.error(f"Error clearing all vectors: {e}")
            return 0

    def delete_orphan_vectors(self, db: Session) -> int:
        """
        删除孤儿向量（向量库中存在但数据库中不存在的文档的向量）

        Args:
            db: 数据库会话

        Returns:
            int: 删除的向量数量
        """
        try:
            from app.models.document import CourseDocument

            # 获取向量库中的所有文档ID
            all_data = self.collection.get(include=["metadatas"])
            vector_doc_ids = set()
            if all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    doc_id = metadata.get('document_id')
                    if doc_id:
                        vector_doc_ids.add(doc_id)

            # 获取数据库中的所有文档ID
            db_documents = db.query(CourseDocument.id).all()
            db_doc_ids = set(doc.id for doc in db_documents)

            # 找出孤儿文档ID
            orphan_doc_ids = vector_doc_ids - db_doc_ids

            if not orphan_doc_ids:
                logger.info("No orphan vectors found")
                return 0

            # 删除孤儿向量
            deleted_count = 0
            for doc_id in orphan_doc_ids:
                success = self.delete_document_vectors(doc_id)
                if success:
                    deleted_count += 1
                    logger.info(f"Deleted orphan vectors for document {doc_id}")

            logger.info(f"Deleted orphan vectors for {deleted_count} documents")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting orphan vectors: {e}")
            return 0

    def clear_all_vectors(self) -> int:
        """
        清空向量库中的所有向量数据

        警告：这是一个危险操作，会删除所有向量数据！

        Returns:
            int: 删除的向量数量
        """
        try:
            # 获取所有向量ID
            all_data = self.collection.get()

            if not all_data or not all_data['ids']:
                logger.info("Vector database is already empty")
                return 0

            vector_count = len(all_data['ids'])
            logger.warning(f"Clearing ALL vectors from database: {vector_count} vectors will be deleted")

            # 删除所有向量
            self.collection.delete(ids=all_data['ids'])

            # 强制持久化
            try:
                self.chroma_client.persist()
                logger.info(f"Successfully cleared {vector_count} vectors and persisted changes")
            except Exception as persist_error:
                logger.warning(f"Failed to persist after clearing: {persist_error}")

            return vector_count

        except Exception as e:
            logger.error(f"Error clearing all vectors: {e}")
            return 0



# 创建全局实例
rag_service = RAGService()
