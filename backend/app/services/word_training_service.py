
import random
import re
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.subsection import SubSection
from app.models.knowledge_point import KnowledgePoint
from app.models.user_word_stats import UserWordStats
from app.core.config import settings
from openai import AsyncOpenAI

class WordTrainingService:
    def __init__(self):
        self.prompt_file_path = r"c:\Users\lala\Desktop\毕设\bishe\ai提示词.txt"
        # Initialize Async Client for concurrency
        self.client = None
        
    def _get_client(self):
        if not self.client:
            self.client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_API_KEY,
                base_url=settings.LLM_BASE_URL if settings.LLM_PROVIDER == "deepseek" else settings.LLM_BASE_URL,
            )
        return self.client

    def get_subsection_type(self, db: Session, subsection_id: int) -> str:
        """
        获取小节的知识点类型。
        检查小节下关联的第一个 KnowledgePoint 的类型。
        如果未找到，默认为 "word"。
        """
        kp = db.query(KnowledgePoint).filter(KnowledgePoint.subsection_id == subsection_id).first()
        if kp and kp.type:
            return kp.type
        return "word"

    def parse_words_from_subsection(self, db: Session, subsection_id: int) -> List[str]:
        subsection = db.query(SubSection).filter(SubSection.id == subsection_id).first()
        if not subsection or not subsection.content:
            return []
        
        # Remove [] and 【】 content
        content = subsection.content
        # Regex to remove content within brackets including the brackets
        content = re.sub(r'\[.*?\]', '', content)
        content = re.sub(r'【.*?】', '', content)
        
        # Split lines and clean
        lines = content.split('\n')
        
        words = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Filter option lines like "A. ", "B.", "(A)" etc if they are likely garbage from previous quiz docs
            if re.match(r'^[A-D][\.\、\s]', line) or re.match(r'^\([A-D]\)', line):
                 continue
                 
            # Remove leading numbers "1. ", "2. " which are common in word lists
            line = re.sub(r'^\d+[\.\、\s]\s*', '', line)
            
            if line:
                words.append(line)
                
        return words

    def parse_grammar_from_subsection(self, db: Session, subsection_id: int) -> Optional[Dict[str, Any]]:
        """
        解析语法类型的小节内容。
        逻辑：
        1. 移除 [] 和 【】 内容。
        2. 识别核心语法行（不在 {} 内的内容）。
        3. 识别 {} 内的用法列表。
        """
        subsection = db.query(SubSection).filter(SubSection.id == subsection_id).first()
        if not subsection or not subsection.content:
            return None
        
        content = subsection.content
        content = re.sub(r'\[.*?\]', '', content)
        content = re.sub(r'【.*?】', '', content)
        
        # 提取 {} 块
        usages = re.findall(r'\{([\s\S]*?)\}', content)
        
        # 提取核心语法（移除 {} 块后的剩余内容）
        core_content = re.sub(r'\{[\s\S]*?\}', '', content)
        # 清理多余空行
        core_lines = [line.strip() for line in core_content.split('\n') if line.strip()]
        core_text = "\n".join(core_lines)
        
        return {
            "core": core_text,
            "usages": usages
        }

    def select_words_for_user(self, db: Session, user_id: int, words: List[str], count: int, subsection_id: int) -> List[str]:
        if not words:
            return []
            
        # Get stats for these words in this specific subsection
        stmt = select(UserWordStats).where(
            UserWordStats.user_id == user_id,
            UserWordStats.subsection_id == subsection_id,
            UserWordStats.word.in_(words)
        )
        stats = db.scalars(stmt).all()
        stats_map = {s.word: s.count for s in stats}
        
        # Create a list of (word, count)
        # If word not in stats, count is 0
        word_counts = []
        for w in words:
            c = stats_map.get(w, 0)
            word_counts.append((w, c))
        
        # Shuffle first to randomize ties (words with same count)
        random.shuffle(word_counts)
        # Sort by count (asc) - "单词计数少的优先"
        word_counts.sort(key=lambda x: x[1])
        
        # Select top N
        selected = [w for w, c in word_counts[:count]]
        return selected
    
    def load_prompt_templates(self, type_tag: str = "单词") -> List[str]:
        try:
            with open(self.prompt_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find block for [type_tag]
            pattern = re.escape(f"[{type_tag}]") + r"(.*?)(?=\n\s*\[|$)"
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                return []
            
            target_content = match.group(1).strip()
            
            # Find all ( ... ) blocks
            # We use [\s\S]*? to match across newlines non-greedily
            # Support both English () and Chinese （） parentheses
            templates = re.findall(r'[\(\（]([\s\S]*?)[\)\）]', target_content)
            
            # Clean up templates
            templates = [t.strip() for t in templates if t.strip()]
            
            return templates
            
        except Exception as e:
            print(f"Error reading prompts: {e}")
            return []

    async def generate_single_question(self, word: str, template: str) -> Dict[str, Any]:
        client = self._get_client()
        
        # Determine quiz type from template content
        quiz_type_hint = "blank"
        if "选择题" in template or "options" in template:
            quiz_type_hint = "choice"
        elif "默写" in template or "blank" in template:
            quiz_type_hint = "blank"
            
        # Construct prompt
        # The template is now the full user prompt from (...)
        # We replace {} with the word OR append the content if no {} exists
        
        display_prompt = ""
        if "{}" in template:
            display_prompt = template.replace('{}', word)
        else:
            # For grammar or templates without placeholder, append content
            display_prompt = f"{template}\n{word}"

        # We append an instruction to force JSON format for easier parsing and grading
        # Add quiz_type field to JSON requirement
        # Add strict rules to prevent answer leakage and formatting issues
        system_instruction = (
            f"请务必以JSON格式返回结果，字段包括：'question' (题目文本), 'options' (选项数组，如果是填空题则为空), 'answer' (正确答案), 'quiz_type' (固定返回 '{quiz_type_hint}')。\n"
            "重要规则：\n"
            "1. 题目(question)中【绝对不能】包含目标单词的中文释义或正确答案，否则无法起到测试作用。\n"
            "2. 如果输入的目标单词包含中文释义（如'apple 苹果'），请只针对英文部分('apple')出题，并在题目中隐藏中文部分。\n"
            "3. 如果是选择题，选项必须放在'options'数组中，【绝对不能】显示在'question'文本中。\n"
            "4. 不要包含markdown标记。"
        )
        
        final_user_content = f"{display_prompt}\n\n{system_instruction}"
        
        try:
             response = await client.chat.completions.create(
                 model=settings.LLM_MODEL, 
                 messages=[{"role": "user", "content": final_user_content}],
                 temperature=0.7,
                 response_format={"type": "json_object"} # Force JSON if supported by model/proxy
             )
             
             content = response.choices[0].message.content
             
             # Clean markdown code blocks if present
             content = content.strip()
             if content.startswith("```json"):
                 content = content[7:]
             elif content.startswith("```"):
                 content = content[3:]
             
             if content.endswith("```"):
                 content = content[:-3]
                 
             content = content.strip()
             
             return {
                 "word": word,
                 "prompt": display_prompt, # Store only the display prompt
                 "question_content": content,
                 "success": True,
                 "template_type": quiz_type_hint # Return hint for upper layer
             }
        except Exception as e:
            return {"word": word, "error": str(e), "success": False}

    async def generate_word_quiz(self, db: Session, user_id: int, subsection_id: int, count: int) -> List[Dict[str, Any]]:
        # 1. Determine type
        kp_type = self.get_subsection_type(db, subsection_id)
        
        tasks = []
        sem = asyncio.Semaphore(5) # Max 5 concurrent requests
        
        async def bounded_generate(content_item, template_list):
            async with sem:
                template = random.choice(template_list)
                return await self.generate_single_question(content_item, template)

        if kp_type == "grammar":
            # Grammar Logic
            grammar_data = self.parse_grammar_from_subsection(db, subsection_id)
            if not grammar_data:
                raise ValueError("No content found for grammar subsection")
            
            templates = self.load_prompt_templates("语法")
            if not templates:
                raise ValueError("No valid prompt templates found in ai提示词.txt for [语法]")
            
            core = grammar_data["core"]
            usages = grammar_data["usages"]
            
            # Generate 'count' questions
            for _ in range(count):
                # Construct content: Core + Random Usage (if any)
                content_to_use = core
                if usages:
                    usage = random.choice(usages)
                    content_to_use = f"{core}\n{usage}"
                
                tasks.append(bounded_generate(content_to_use, templates))
                
        else:
            # Word Logic (Default)
            words_in_subsection = self.parse_words_from_subsection(db, subsection_id)
            if not words_in_subsection:
                raise ValueError("No words found in subsection content")
                
            selected_words = self.select_words_for_user(db, user_id, words_in_subsection, count, subsection_id)
            if not selected_words:
                raise ValueError("No words available for selection")

            templates = self.load_prompt_templates("单词")
            if not templates:
                raise ValueError("No valid prompt templates found in ai提示词.txt for [单词]")
            
            for word in selected_words:
                tasks.append(bounded_generate(word, templates))
            
        results = await asyncio.gather(*tasks)
        
        # Filter successful results
        valid_results = [r for r in results if r["success"]]
        
        # Update stats: Increment count for generated words (Only for Word type for now)
        # Or should we track grammar usage? 
        # Since grammar prompts are dynamic combinations, tracking might be tricky.
        # But if the user wants stats, we can track the "Core Grammar" title as the 'word' key.
        # Let's keep it simple: only track for 'word' type or if it looks like a word.
        if kp_type == "word":
            for r in valid_results:
                word = r["word"]
                stat = db.query(UserWordStats).filter(
                    UserWordStats.user_id == user_id,
                    UserWordStats.subsection_id == subsection_id,
                    UserWordStats.word == word
                ).first()
                if not stat:
                    stat = UserWordStats(user_id=user_id, subsection_id=subsection_id, word=word, count=0)
                    db.add(stat)
                
                stat.count += 1
            db.commit()
        
        return valid_results

    def update_stats_after_submission(self, db: Session, user_id: int, word: str, is_correct: bool, subsection_id: int):
        """
        如果这个单词的出的题答题正确了则无需处理 (Net +1 from generation)
        如果这个单词出的题错误了则这个单词的计数-1 (Net 0)
        """
        if is_correct:
            return # No change needed
        
        # If wrong, decrement count
        stat = db.query(UserWordStats).filter(
            UserWordStats.user_id == user_id,
            UserWordStats.subsection_id == subsection_id,
            UserWordStats.word == word
        ).first()
        
        if stat and stat.count > 0:
            stat.count -= 1
            db.commit()

word_training_service = WordTrainingService()
