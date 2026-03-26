"""
向量数据重置与重建脚本

【脚本用途】
本脚本用于重置和重建 ChromaDB 向量数据库中的所有向量数据。
当向量数据出现问题或需要更换 Embedding 模型时，可以使用此脚本重建向量索引。

【使用场景】
1. 向量数据损坏：ChromaDB 数据出现异常，需要重建
2. 更换 Embedding 模型：更换了向量化模型后，需要重新生成所有向量
3. 数据迁移：从其他环境迁移数据后，需要重建向量索引
4. 测试环境重置：开发/测试时需要清空并重建向量数据

【执行流程】
1. 清空 ChromaDB 中的所有向量数据
2. 重置数据库中的向量化标志（is_vectorized = 0）
3. 重新向量化所有课程文档（CourseDocument）
4. 重新向量化所有小节内容（SubSection）

【使用方法】
在 backend 目录下执行：
    python scripts/reset_vectors.py

【注意事项】
⚠️ 此操作会清空所有向量数据，请谨慎使用！
⚠️ 执行时间取决于文档数量，可能需要较长时间
⚠️ 建议在非高峰期执行，避免影响系统性能
⚠️ 执行前请确保数据库连接正常，Embedding API 可用

【依赖】
- ChromaDB：向量数据库
- Embedding API：用于生成向量（配置在 settings.EMBEDDING_API_KEY）
- 数据库：MySQL（存储文档和向量化状态）

【输出】
脚本会输出详细的执行日志，包括：
- 清空的向量数量
- 处理的文档/小节数量
- 成功/失败统计

【示例输出】
    Connecting to database: mysql+pymysql://...
    Clearing ChromaDB...
    Cleared 150 vectors from ChromaDB.
    Resetting is_vectorized flags in database...
    Reset flags for documents.
    Re-vectorizing documents...
    Found 45 documents to vectorize.
    Processing document 1/45: Unit 1 Introduction (ID: 1)...
      Successfully vectorized document 1
    ...
    Finished vectorizing documents. Success: 45/45.
    Vectorizing SubSections...
    Found 30 subsections to vectorize.
    ...
    Finished vectorizing subsections. Success: 30/30.

【作者】系统管理员
【创建日期】2026-01-12
【最后更新】2026-03-26
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.document import CourseDocument
from app.models.subsection import SubSection
from app.services.rag_service import rag_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_vectors():
    """
    重置并重建所有向量数据
    
    执行步骤：
    1. 清空 ChromaDB 向量数据库
    2. 重置数据库中的向量化标志
    3. 重新向量化所有课程文档
    4. 重新向量化所有小节内容
    """
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # ========================================
        # 步骤 1: 清空 ChromaDB 向量数据库
        # ========================================
        print("Clearing ChromaDB...")
        try:
            count = rag_service.clear_all_vectors()
            print(f"Cleared {count} vectors from ChromaDB.")
        except Exception as e:
            print(f"Error clearing ChromaDB: {e}")

        # ========================================
        # 步骤 2: 重置数据库中的向量化标志
        # ========================================
        print("Resetting is_vectorized flags in database...")
        # Use execute with text() for update
        stmt = text("UPDATE course_documents SET is_vectorized = 0, vector_count = 0, chroma_ids = NULL")
        result = db.execute(stmt)
        db.commit()
        print(f"Reset flags for documents.")

        # ========================================
        # 步骤 3: 重新向量化所有课程文档
        # ========================================
        print("Re-vectorizing documents...")
        docs = db.query(CourseDocument).filter(CourseDocument.content.isnot(None)).all()
        print(f"Found {len(docs)} documents to vectorize.")

        success_count = 0
        for i, doc in enumerate(docs):
            print(f"Processing document {i+1}/{len(docs)}: {doc.title} (ID: {doc.id})...")
            try:
                # We need to use vectorize_document method
                # Note: vectorize_document commits to DB, so we should be careful with session
                if rag_service.vectorize_document(db, doc.id):
                    success_count += 1
                    print(f"  Successfully vectorized document {doc.id}")
                else:
                    print(f"  Failed to vectorize document {doc.id}")
            except Exception as e:
                print(f"  Error processing document {doc.id}: {e}")

        print(f"Finished vectorizing documents. Success: {success_count}/{len(docs)}.")

        # ========================================
        # 步骤 4: 重新向量化所有小节内容
        # ========================================
        print("Vectorizing SubSections...")
        subsections = db.query(SubSection).filter(SubSection.content.isnot(None)).all()
        print(f"Found {len(subsections)} subsections to vectorize.")

        sub_success_count = 0
        for i, sub in enumerate(subsections):
            print(f"Processing subsection {i+1}/{len(subsections)}: {sub.title} (ID: {sub.id})...")
            try:
                if rag_service.vectorize_subsection(db, sub.id):
                    sub_success_count += 1
                    print(f"  Successfully vectorized subsection {sub.id}")
                else:
                    print(f"  Failed to vectorize subsection {sub.id}")
            except Exception as e:
                print(f"  Error processing subsection {sub.id}: {e}")
        
        print(f"Finished vectorizing subsections. Success: {sub_success_count}/{len(subsections)}.")
        
        # ========================================
        # 执行完成总结
        # ========================================
        print("\n" + "="*60)
        print("Vector reset completed!")
        print(f"Documents: {success_count}/{len(docs)} successful")
        print(f"SubSections: {sub_success_count}/{len(subsections)} successful")
        print("="*60)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("Vector Reset Script")
    print("="*60)
    print("⚠️  WARNING: This will clear all vector data and rebuild!")
    print("⚠️  This operation may take a long time.")
    print("="*60)
    
    # 简单的确认提示
    try:
        response = input("Do you want to continue? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            reset_vectors()
        else:
            print("Operation cancelled.")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
