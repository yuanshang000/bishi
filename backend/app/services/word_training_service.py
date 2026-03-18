
import random
import re
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.subsection import SubSection
from app.models.knowledge_point import KnowledgePoint
from app.models.user_word_stats import UserWordStats
from app.models.user_knowledge_stats import UserKnowledgePointStats
from app.core.config import settings
from openai import AsyncOpenAI

class WordTrainingService:
    def __init__(self):
        self.prompt_file_path = r"c:\Users\lala\Desktop\毕设\bishe\ai提示词.txt"
        # Initialize Async Client for concurrency
        self.client = None
        
    def _get_client(self):
        if not self.client:
            # Use a longer timeout for generation tasks
            timeout = getattr(settings, "LLM_TIMEOUT", 60.0)
            if timeout < 60:
                timeout = 60.0

            # 统一使用环境变量配置
            api_key = settings.DEEPSEEK_API_KEY if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_API_KEY

            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.LLM_BASE_URL,
                timeout=timeout
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

    def get_weak_content_for_subsection(self, db: Session, user_id: int, subsection_id: int) -> List[str]:
        """
        获取指定小节中用户的薄弱知识点内容（正确率 < 60%）
        """
        # Query stats joined with KnowledgePoint
        results = db.query(UserKnowledgePointStats, KnowledgePoint).join(
            KnowledgePoint, UserKnowledgePointStats.knowledge_point_id == KnowledgePoint.id
        ).filter(
            UserKnowledgePointStats.user_id == user_id,
            KnowledgePoint.subsection_id == subsection_id,
            UserKnowledgePointStats.total_attempts > 0
        ).all()
        
        weak_contents = []
        for stats, kp in results:
            accuracy = stats.correct_attempts / stats.total_attempts
            if accuracy < 0.6:
                weak_contents.append(kp.content)
                
        return weak_contents

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
            "1. 对于默写/填空题，题目中【必须】包含目标单词的中文意思，例如：'单词默写，中文意思：\"抛弃\"\\n请默写英文单词：______'。\n"
            "2. 题目中【绝对不能】包含正确答案（英文单词），否则无法起到测试作用。\n"
            "3. 如果是选择题，选项必须放在'options'数组中，【绝对不能】显示在'question'文本中。\n"
            "4. 不要包含markdown标记。"
        )
        
        final_user_content = f"{display_prompt}\n\n{system_instruction}"
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
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
                last_error = str(e)
                print(f"Attempt {attempt + 1}/{max_retries} failed for word '{word}': {e}")
                # Wait a bit before retrying
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        
        return {"word": word, "error": f"Failed after {max_retries} attempts. Last error: {last_error}", "success": False}

    async def generate_word_quiz(self, db: Session, user_id: int, subsection_id: int, count: int, practice_mode: str = 'subsection') -> List[Dict[str, Any]]:
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
            weak_contents = []
            if practice_mode == 'comprehensive':
                weak_contents = self.get_weak_content_for_subsection(db, user_id, subsection_id)
            
            if weak_contents:
                # Use weak grammar points
                templates = self.load_prompt_templates("语法")
                if not templates:
                    raise ValueError("No valid prompt templates found in ai提示词.txt for [语法]")
                
                # Generate questions for each weak point (up to count)
                # If weak points are fewer than count, we might loop or just return fewer?
                # User probably wants to practice these specifically.
                # If more weak points than count, sample them?
                selected_contents = weak_contents
                if len(selected_contents) > count:
                    selected_contents = random.sample(selected_contents, count)
                
                for content in selected_contents:
                    tasks.append(bounded_generate(content, templates))
                    
                # If we have fewer weak points than count, should we fill up with others?
                # User said "Recommended training is to train THESE weak points".
                # So maybe strict adherence is better.
                
            else:
                # Standard Grammar Logic
                grammar_data = self.parse_grammar_from_subsection(db, subsection_id)
                if not grammar_data:
                    # Try to fetch weak points if parsing failed? No, parsing failed means no content.
                    # But wait, get_weak_content uses KnowledgePoint table.
                    # If parse_grammar uses subsection.content.
                    # They should be consistent.
                    # If comprehensive mode but no weak points found, maybe fallback to standard?
                    # The 'else' block here handles:
                    # 1. practice_mode != 'comprehensive'
                    # 2. practice_mode == 'comprehensive' but no weak points found (fallback)
                    
                    if practice_mode == 'comprehensive':
                         # If specifically asked for comprehensive but no weak points,
                         # maybe we should just generate random ones from the subsection?
                         # Or return empty?
                         # Let's fallback to standard generation to ensure user gets something.
                         pass
                    
                    # Re-check grammar_data if we are here (it might be None if we didn't call parse yet)
                    if 'grammar_data' not in locals():
                         grammar_data = self.parse_grammar_from_subsection(db, subsection_id)
                         
                if not grammar_data:
                     raise ValueError("No content found for grammar subsection")

                templates = self.load_prompt_templates("语法")
                if not templates:
                    raise ValueError("No valid prompt templates found in ai提示词.txt for [语法]")
                
                core = grammar_data["core"]
                usages = grammar_data["usages"]
                
                # Generate 'count' questions using batch mode to avoid duplicates
                if count > 1:
                    # Batch generation: generate all questions at once to ensure diversity
                    batch_task = self._generate_grammar_batch(core, usages, count, templates)
                    tasks.append(batch_task)
                else:
                    # Single question: use original logic
                    content_to_use = core
                    if usages:
                        usage = random.choice(usages)
                        content_to_use = f"{core}\n{usage}"
                    tasks.append(bounded_generate(content_to_use, templates))
                
        else:
            # Word Logic (Default)
            selected_words = []
            
            if practice_mode == 'comprehensive':
                 weak_words = self.get_weak_content_for_subsection(db, user_id, subsection_id)
                 if weak_words:
                     # If we have weak words, use them.
                     # Sort by some metric? get_weak_content returns list of strings.
                     # Maybe random sample if too many?
                     if len(weak_words) > count:
                         selected_words = random.sample(weak_words, count)
                     else:
                         selected_words = weak_words
            
            if not selected_words:
                # Fallback or Standard Mode
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
        
        if not valid_results and tasks:
            # If we had tasks but no valid results, it means all failed.
            errors = [r.get("error") for r in results if not r.get("success")]
            raise ValueError(f"Failed to generate questions. Errors: {errors[:1]}")
        
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

    async def _generate_grammar_batch(self, core: str, usages: List[str], count: int, templates: List[str]) -> Dict[str, Any]:
        """
        批量生成语法题目，避免重复
        
        Args:
            core: 核心语法内容
            usages: 用法列表
            count: 需要生成的题目数量
            templates: 提示词模板列表
            
        Returns:
            Dict: 批量生成结果
        """
        client = self._get_client()
        
        # 构建批量生成的提示词
        template = random.choice(templates)
        
        # 构建多样化的用法示例
        usage_examples = ""
        if usages:
            usage_examples = "\n用法示例：\n" + "\n".join(f"- {usage}" for usage in usages[:5])
        
        # 构建批量生成提示词
        batch_prompt = f"""{template}

语法内容：
{core}
{usage_examples}

**重要要求：**
请一次性生成 {count} 道**互不相同**的语法选择题，确保：
1. 每道题考察不同的句子场景
2. 每道题使用不同的词汇和表达
3. 每道题的干扰项设计要合理且不同
4. 所有题目必须严格基于上述语法内容

请以JSON数组格式返回 {count} 道题目，格式如下：
[
  {{
    "question": "题目内容...",
    "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}},
    "answer": "正确答案(A/B/C/D)",
    "quiz_type": "choice"
  }},
  ...
]

不要包含markdown标记，直接返回JSON数组。"""
        
        try:
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": batch_prompt}],
                temperature=0.8,  # 提高温度以增加多样性
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # 清理markdown标记
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # 解析JSON数组
            import json
            import re
            
            try:
                questions = json.loads(content)
            except json.JSONDecodeError:
                # 尝试修复常见的JSON错误
                content = re.sub(r',\s*}', '}', content)
                content = re.sub(r',\s*]', ']', content)
                questions = json.loads(content)
            
            # 确保返回的是数组
            if not isinstance(questions, list):
                questions = [questions]
            
            # 转换为单题格式，与原有接口兼容
            # 这里我们只返回第一题的格式，其他题目通过扩展方式处理
            if len(questions) > 0:
                return {
                    "word": "grammar_batch",
                    "prompt": batch_prompt,
                    "question_content": json.dumps(questions[0], ensure_ascii=False),
                    "success": True,
                    "template_type": "choice",
                    "batch_questions": questions  # 额外保存批量题目
                }
            else:
                raise ValueError("No questions generated")
                
        except Exception as e:
            logger.error(f"Batch grammar generation error: {e}")
            # 降级到逐个生成
            raise

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
