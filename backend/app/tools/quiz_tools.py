from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def generate_interactive_quiz(
    db: Session,
    topic: str,
    count: int = 3,
    quiz_type: str = "mixed",
    difficulty: str = "intermediate",
    student_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    根据用户的主题或提示词生成互动练习题。
    """
    # Import inside function to avoid circular import
    from app.services.llm_service import llm_service
    from app.services.rag_service import rag_service

    logger.info(f"Generating interactive quiz for topic: {topic}, count: {count}, type: {quiz_type}, difficulty: {difficulty}")

    try:
        # 1. RAG Search to get context
        # 检查是否包含明确的章节引用（如“【参考：...】”）
        # 这种引用通常由前端Chapter Selector注入
        
        # 提取 topic 中的关键信息，如果包含章节引用，提取出来用于增强搜索
        import re
        chapter_ref_match = re.search(r'【参考：(.*?)】', topic)
        
        search_query = topic
        if chapter_ref_match:
            # 如果有章节引用，直接使用章节标题作为搜索关键词，权重更高
            search_query = chapter_ref_match.group(1)
            logger.info(f"Detected chapter reference: {search_query}, using as primary search query.")
        
        # Try to find relevant content based on topic
        context, used_docs, _ = rag_service.get_context_for_query(query=search_query, max_length=3000)
        
        # If no context found, use the topic itself as context/instruction
        if not context:
            logger.info("No RAG context found, using topic as context.")
            context = f"Topic/Prompt: {topic}"
        else:
            logger.info(f"Found {len(used_docs)} documents for context.")


        # 2. Generate Quiz using LLM service
        questions = llm_service.generate_custom_quiz(
            context=context,
            quiz_type=quiz_type,
            count=count,
            difficulty=difficulty
        )

        # 3. Return formatted response
        response = {
            "generate_interactive_quiz_response": {
                "count": len(questions),
                "questions": questions,
                "topic": topic,
                "quiz_id": 0, # Temporary ID, not saved to DB yet
                "quiz_type": quiz_type,
                "difficulty": difficulty
            }
        }
        
        # 强制将 response 序列化为 JSON 字符串返回，确保前端能正确解析
        # 注意：这里我们返回 dict，LLM Service 会将其序列化为 JSON 字符串
        return response

    except Exception as e:
        logger.error(f"Error generating interactive quiz: {e}", exc_info=True)
        return {
            "generate_interactive_quiz_response": {
                "error": str(e),
                "count": 0,
                "questions": [],
                "topic": topic
            }
        }
