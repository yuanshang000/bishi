import re
import json
import logging
import io
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection
from app.models.knowledge_point import KnowledgePoint
from app.services.llm_service import LLMService
from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)

from sqlalchemy.exc import IntegrityError

class CourseParserService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    def parse_with_strict_rules(self, content: str, target_chapter_id: Optional[int] = None) -> Optional[Chapter]:
        """
        使用严格的正则规则解析课程文档 (Based on ewai2.md)
        
        Args:
            content: 文档内容
            target_chapter_id: 目标章节ID (如果指定，则解析到该章节下)
            
        Returns:
            Chapter: 解析/更新后的章节对象
        """
        lines = content.split('\n')
        
        current_chapter = None
        current_section = None
        current_subsection = None
        current_kp_type = None
        
        # Regex Patterns
        # Allow for optional content (like numbering) before the marker
        chapter_pattern = re.compile(r'^.*?\[章节\]\s*(.*)')
        section_pattern = re.compile(r'^.*?\[节\]\s*(.*)')
        subsection_pattern = re.compile(r'^.*?\[小目标\]\s*(.*)')
        
        # Knowledge Point Markers
        # Allow for optional content before the marker
        kp_word_marker = re.compile(r'^.*?\[知识点:单词\]\s*(.*)')
        kp_grammar_marker = re.compile(r'^.*?\[知识点:语法\]\s*(.*)')
        kp_phrase_marker = re.compile(r'^.*?\[知识点:搭配\]\s*(.*)')
        
        # Initialize target chapter if provided
        if target_chapter_id:
            current_chapter = self.db.query(Chapter).filter(Chapter.id == target_chapter_id).first()
            if not current_chapter:
                raise ValueError(f"Target chapter {target_chapter_id} not found")
            logger.info(f"Parsing content into target chapter: {current_chapter.title}")

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 1. Chapter
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                title = chapter_match.group(1).strip()
                
                if target_chapter_id:
                    # Update existing chapter title
                    current_chapter.title = title
                    self.db.add(current_chapter)
                else:
                    # Create new chapter
                    # Check if exists by title to avoid duplicates in this session? 
                    # Better to check DB.
                    # Simplified: Create new one.
                    c_num = self.db.query(Chapter).count() + 1
                    current_chapter = Chapter(chapter_number=c_num, title=title)
                    self.db.add(current_chapter)
                
                self.db.commit()
                self.db.refresh(current_chapter)
                current_section = None
                current_subsection = None
                continue
                
            if current_chapter and ("章节目标" in line or "章节 目标" in line):
                parts = line.split("：", 1) if "：" in line else line.split(":", 1)
                if len(parts) > 1:
                    current_chapter.description = parts[1].strip()
                    self.db.add(current_chapter)
                    self.db.commit()
                    self.db.refresh(current_chapter)
                continue
                
            # 2. Section
            section_match = section_pattern.match(line)
            if section_match:
                if not current_chapter:
                    logger.warning(f"Line {i}: Section found without Chapter context")
                    continue
                    
                title = section_match.group(1).strip()
                order = self.db.query(Section).filter(Section.chapter_id == current_chapter.id).count() + 1
                current_section = Section(chapter_id=current_chapter.id, title=title, order=order)
                self.db.add(current_section)
                self.db.commit()
                self.db.refresh(current_section)
                current_subsection = None
                continue
                
            # 3. Subsection
            subsection_match = subsection_pattern.match(line)
            if subsection_match:
                if not current_section:
                    logger.warning(f"Line {i}: Subsection found without Section context")
                    continue
                
                title = subsection_match.group(1).strip()
                
                # Extract metadata from following lines if they exist
                # Look ahead for metadata bullets
                description = None
                weight = 0.0
                passing_score = 60.0
                
                # Simple lookahead for metadata
                # We'll just set defaults here, and let the loop handle metadata lines if we encounter them
                # But wait, the loop processes line by line. 
                # If we encounter a metadata line, we should update the current_subsection.
                
                order = self.db.query(SubSection).filter(SubSection.section_id == current_section.id).count() + 1
                current_subsection = SubSection(
                    section_id=current_section.id, 
                    title=title, 
                    order=order,
                    content="" # Will accumulate content
                )
                self.db.add(current_subsection)
                self.db.commit()
                self.db.refresh(current_subsection)
                current_kp_type = None
                continue
                
            # Metadata parsing (Description, Weight, Passing Score)
            if current_subsection:
                # Target Description
                if "●目标描述" in line or "● 目标描述" in line:
                    parts = line.split("：", 1) if "：" in line else line.split(":", 1)
                    if len(parts) > 1:
                        current_subsection.description = parts[1].strip()
                        self.db.add(current_subsection)
                        self.db.commit()
                    continue
                
                # Weight
                if "●权重占比" in line or "● 权重占比" in line:
                    parts = line.split("：", 1) if "：" in line else line.split(":", 1)
                    if len(parts) > 1:
                        # Extract number, handle '%'
                        val_str = parts[1].strip().replace('%', '')
                        try:
                            current_subsection.weight = float(val_str)
                            self.db.add(current_subsection)
                            self.db.commit()
                        except ValueError:
                            pass
                    continue
                    
                # Passing Score
                if "●合格分数" in line or "● 合格分数" in line:
                    parts = line.split("：", 1) if "：" in line else line.split(":", 1)
                    if len(parts) > 1:
                        # Extract number, handle '分'
                        val_str = parts[1].strip().replace('分', '')
                        try:
                            current_subsection.passing_score = float(val_str)
                            self.db.add(current_subsection)
                            self.db.commit()
                        except ValueError:
                            pass
                    continue

                # Min Questions
                if "●最少题数" in line or "● 最少题数" in line:
                    parts = line.split("：", 1) if "：" in line else line.split(":", 1)
                    if len(parts) > 1:
                        # Extract number, handle '道' or '题'
                        val_str = parts[1].strip().replace('道', '').replace('题', '')
                        try:
                            current_subsection.min_questions = int(val_str)
                            self.db.add(current_subsection)
                            self.db.commit()
                        except ValueError:
                            pass
                    continue

            # 4. Knowledge Points
            if not current_subsection:
                continue
                
            # Accumulate text content for the subsection
            current_subsection.content = (current_subsection.content or "") + line + "\n"
            
            # Check markers
            word_match = kp_word_marker.match(line)
            if word_match:
                current_kp_type = "word"
                content = word_match.group(1).strip()
                if content:
                    self._create_kp(current_subsection.id, content, "word")
                continue

            grammar_match = kp_grammar_marker.match(line)
            if grammar_match:
                current_kp_type = "grammar"
                content = grammar_match.group(1).strip()
                if content:
                    self._create_kp(current_subsection.id, content, "grammar")
                continue
            
            phrase_match = kp_phrase_marker.match(line)
            if phrase_match:
                current_kp_type = "phrase"
                content = phrase_match.group(1).strip()
                if content:
                    self._create_kp(current_subsection.id, content, "phrase")
                continue
                
            # Parse Knowledge Point Content (continuation lines)
            if current_kp_type:
                # Filter out obvious non-content lines if necessary
                if line.startswith("-") or line.startswith("*") or len(line) > 1:
                    self._create_kp(current_subsection.id, line, current_kp_type)
        
        return current_chapter

    def _create_kp(self, subsection_id: int, content: str, kp_type: str):
        if not subsection_id:
            logger.warning(f"Skipping knowledge point '{content}' because subsection_id is None")
            return
            
        kp = KnowledgePoint(
            subsection_id=subsection_id,
            content=content,
            type=kp_type,
            priority_score=0.0
        )
        self.db.add(kp)
        self.db.commit()

    def parse_unstructured_content(self, text: str) -> str:
        """
        使用LLM解析非结构化内容为指定格式
        """
        llm = LLMService()
        
        prompt = """
        请将以下课程内容转换为指定的目标导向格式。
        
        目标格式要求：
        1. 使用 [章节] 标题 表示章节
        2. 使用 [节] 标题 表示小节
        3. 使用 [小目标] 标题 表示学习小目标
        4. 在小目标下方，提取并列出知识点：
           - [知识点:单词] 单词内容 (格式: 单词 (词性) 中文含义 [例句: ...])
           - [知识点:语法] 语法内容
           - [知识点:搭配] 搭配内容
           
        示例输出：
        [章节] 英语基础
        [节] 基础词汇
        [小目标] 掌握核心名词
        [知识点:单词] apple (n.) 苹果 [例句: An apple a day keeps the doctor away.]
        [知识点:单词] banana (n.) 香蕉 [例句: Monkeys love bananas.]
        [小目标] 基础语法
        [知识点:语法] 一般现在时: 表示习惯性动作 [例: I go to school every day.]
        
        请处理以下内容（如果内容较长，请合理分章节）：
        """
        
        # 截断过长的文本防止超出token限制 (简单策略)
        # 实际生产中可能需要分块处理，这里简化为只处理前10000字符
        truncated_text = text[:50000]
        
        messages = [
            {"role": "system", "content": "你是一个严格的课程结构化解析器。你的任务是提取结构，而不是改写内容。对于【核心内容】部分，必须原文照抄，禁止总结。"},
            {"role": "user", "content": prompt + "\n\n" + truncated_text}
        ]
        
        try:
            response = llm.chat(messages, temperature=0.1)
            # 简单的清洗，确保没有markdown代码块包裹
            response = re.sub(r'^```markdown\s*', '', response)
            response = re.sub(r'\s*```$', '', response)
            return response
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise Exception("AI结构化解析失败")

    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        从不同格式的文件中提取文本
        """
        if filename.lower().endswith('.pdf'):
            return self._extract_text_from_pdf(file_content)
        elif filename.lower().endswith('.docx'):
            return self._extract_text_from_docx(file_content)
        elif filename.lower().endswith('.md') or filename.lower().endswith('.txt'):
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file format: {filename}")

    def _extract_text_from_pdf(self, content: bytes) -> str:
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise ValueError("Failed to extract text from PDF")

    def _extract_text_from_docx(self, content: bytes) -> str:
        try:
            docx_file = io.BytesIO(content)
            doc = Document(docx_file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            raise ValueError("Failed to extract text from DOCX")

    def _generate_friendly_requirements(self, json_str: str) -> str:
        """
        生成用户友好的要求描述
        """
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return str(data)
            
            parts = []
            
            # Common keys mapping
            key_map = {
                "type": "题型",
                "types": "题型",
                "count": "数量",
                "difficulty": "难度",
                "tags": "标签",
                "knowledge_points": "知识点",
                "focus": "重点",
                "description": "说明",
                "keywords": "关键词",
                "grammar": "语法点"
            }
            
            for k, v in data.items():
                if k in ['categorized', 'difficulty']:
                    continue
                label = key_map.get(k, k)
                if isinstance(v, list):
                    val = "、".join(map(str, v))
                elif isinstance(v, dict):
                    val = json.dumps(v, ensure_ascii=False)
                else:
                    val = str(v)
                parts.append(f"{label}: {val}")
            
            return "；".join(parts)
        except:
            return "解析失败"
