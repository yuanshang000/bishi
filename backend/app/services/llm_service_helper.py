"""
LLM服务辅助方法
"""
from typing import List, Dict, Any
import difflib

def filter_duplicate_questions(
    new_questions: List[Dict[str, Any]],
    existing_questions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    过滤重复题目
    
    Args:
        new_questions: 新生成的题目
        existing_questions: 已有的题目
    
    Returns:
        List[Dict]: 去重后的题目列表
    """
    if not existing_questions:
        return new_questions
    
    unique_questions = []
    
    for new_q in new_questions:
        is_duplicate = False
        
        # 提取新题目的关键文本
        new_text = _extract_question_text(new_q)
        
        #检查是否与已有题目重复
        for exist_q in existing_questions:
            exist_text = _extract_question_text(exist_q)
            
            # 使用文本相似度判断
            similarity = difflib.SequenceMatcher(None, new_text, exist_text).ratio()
            
            if similarity > 0.7:  # 相似度超过70%认为是重复
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_questions.append(new_q)
    
    return unique_questions

def _extract_question_text(question: Dict[str, Any]) -> str:
    """提取题目的关键文本用于比较"""
    if 'passage' in question:  # 阅读题
        return question.get('passage', '')[:200]
    elif 'audio_text' in question:  # 听力题
        return question.get('audio_text', '')[:200]
    elif 'topic' in question:  # 写作题
        return question.get('topic', '')
    else:  # 翻译题等
        return question.get('question', '')[:100]
