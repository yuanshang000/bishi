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
        # Try to find relevant content based on topic
        context, used_docs, _ = rag_service.get_context_for_query(query=topic, max_length=3000)
        
        # If no context found, use the topic itself as context/instruction
        if not context:
            logger.info("No RAG context found, using topic as context.")
            context = f"Topic/Prompt: {topic}"
        else:
            logger.info(f"Found {len(used_docs)} documents for context.")

        # 2. Generate Quiz using LLM service
        questions = llm_service.generate_quiz(
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
        
        return response

    except Exception as e:
        logger.error(f"Error generating interactive quiz: {e}", exc_info=True)
        return {
            "error": str(e),
            "generate_interactive_quiz_response": {
                "count": 0,
                "questions": [],
                "topic": topic,
                "error": "Failed to generate quiz."
            }
        }
