
import random
import re
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.subsection import SubSection
from app.models.knowledge_point import KnowledgePoint
from app.core.config import settings
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class ComprehensiveQuizService:
    def __init__(self):
        self.prompt_file_path = r"c:\Users\lala\Desktop\毕设\bishe\ai综合出题提示词.txt"
        self.client = None

    def _get_client(self):
        if not self.client:
            # Use a longer timeout for comprehensive generation tasks
            timeout = getattr(settings, "LLM_TIMEOUT", 60.0)
            if timeout < 60:
                timeout = 60.0
                
            self.client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_API_KEY,
                base_url=settings.LLM_BASE_URL if settings.LLM_PROVIDER == "deepseek" else settings.LLM_BASE_URL,
                timeout=timeout
            )
        return self.client

    def _get_subsection_type(self, db: Session, subsection_id: int) -> str:
        kp = db.query(KnowledgePoint).filter(KnowledgePoint.subsection_id == subsection_id).first()
        if kp and kp.type:
            return kp.type
        return "word"

    def _format_subsection_content(self, db: Session, subsection: SubSection) -> str:
        if not subsection.content:
            return ""
        
        # Clean content: remove 【...】 and [...]
        content = re.sub(r'【.*?】', '', subsection.content)
        content = re.sub(r'\[.*?\]', '', content)
        
        stype = self._get_subsection_type(db, subsection.id)
        
        header = ""
        if stype == "word":
            header = "[知识点:单词]"
        elif stype == "grammar":
            header = "[知识点:语法]"
        else:
            header = f"[知识点:{stype}]"
            
        return f"{header}\n{content.strip()}\n"

    def get_section_knowledge(self, db: Session, section_id: int) -> str:
        subsections = db.query(SubSection).filter(SubSection.section_id == section_id).order_by(SubSection.order).all()
        
        full_content = ""
        for sub in subsections:
            full_content += self._format_subsection_content(db, sub) + "\n"
            
        return full_content

    def load_comprehensive_templates(self) -> List[str]:
        try:
            with open(self.prompt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = re.search(r'\[综合训练\](.*?)(\[|$)', content, re.DOTALL)
            if not match:
                logger.error("No [综合训练] block found in prompt file")
                return []
            
            block_content = match.group(1)
            templates = re.findall(r'/\*(.*?)\*/', block_content, re.DOTALL)
            return [t.strip() for t in templates if t.strip()]
            
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {e}")
            return []

    async def generate_single_question(self, knowledge_content: str, template: str, difficulty: str) -> Dict[str, Any]:
        prompt = template.replace("{}", difficulty)
        prompt += f"\n\n下面是知识内容：\n{knowledge_content}"
        
        system_prompt = """
你是一个专业的英语出题专家。
请根据用户的要求和提供的知识内容生成一道题目。
必须返回符合以下JSON格式的数据（不要包含Markdown代码块标记）：
{
    "quiz_type": "题型(translation/writing/reading/choice/listening)",
    "question_text": "题目具体问题（例如：What is the main idea?）",
    "options": {"A": "选项A内容", "B": "选项B内容", "C": "...", "D": "..."} (如果是选择题或阅读理解题),
    "passage": "文章内容" (如果是阅读理解题),
    "requirements": ["要求1", "要求2"] (如果是写作题),
    "word_count": "字数要求" (如果是写作题),
    "correct_answer": "参考答案",
    "explanation": "解析"
}
对于中译英翻译题，quiz_type应为"translation"。
对于英语写作题，quiz_type应为"writing"。
对于阅读理解题，quiz_type应为"reading"。
"""

        client = self._get_client()
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                content = response.choices[0].message.content
                # Clean markdown code blocks if present
                content = re.sub(r'^```json\s*', '', content)
                content = re.sub(r'^```\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
                
                try:
                    data = json.loads(content)
                    # Ensure meta info is included
                    if "meta" not in data:
                        data["meta"] = {
                            "word": knowledge_content[:200] + "..." if len(knowledge_content) > 200 else knowledge_content,
                            "prompt": prompt
                        }
                    return data
                except json.JSONDecodeError:
                    logger.error(f"JSON Parse Error: {content}")
                    # If JSON fails, maybe retry? Or return error.
                    # Usually LLM might output text preamble.
                    # Let's try to extract JSON from text if simple load fails
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(0))
                            if "meta" not in data:
                                data["meta"] = {
                                    "word": knowledge_content[:200] + "..." if len(knowledge_content) > 200 else knowledge_content,
                                    "prompt": prompt
                                }
                            return data
                        except:
                            pass
                    
                    if attempt < max_retries - 1:
                        continue # Retry generation
                    return {"error": "JSON parse error", "raw": content}
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"LLM generation failed (Attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        
        return {"error": f"Generation failed after {max_retries} attempts: {last_error}"}

    async def generate_quiz(self, db: Session, section_id: int, difficulty: str, count: int) -> Dict[str, Any]:
        knowledge = self.get_section_knowledge(db, section_id)
        if not knowledge:
             return {"error": "该章节暂无知识点内容"}

        templates = self.load_comprehensive_templates()
        if not templates:
            return {"error": "未找到综合训练题目模板"}
            
        tasks = []
        # Concurrency control
        sem = asyncio.Semaphore(5)

        async def run_task():
            async with sem:
                template = random.choice(templates)
                return await self.generate_single_question(knowledge, template, difficulty)

        for _ in range(count):
            tasks.append(run_task())
            
        results = await asyncio.gather(*tasks)
        
        # Filter successful questions
        questions = [q for q in results if "error" not in q]
        
        return {
            "questions": questions,
            "total_generated": len(questions),
            "requested": count
        }

comprehensive_quiz_service = ComprehensiveQuizService()
