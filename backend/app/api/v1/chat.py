"""
问答相关API路由
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime

from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage, QuizSubmissionRequest
from app.models.user import User
from app.models.chat import ChatHistory
from app.api.dependencies import get_db, get_current_active_user
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["问答"])


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    发送聊天消息

    - **message**: 用户消息
    - **chapter_id**: 章节ID（可选，用于RAG检索）
    - **session_id**: 会话ID（可选，用于维护上下文）
    - **use_rag**: 是否使用RAG检索（默认True）
    - **mode**: 模式 (chat/quiz)
    """
    # 生成或使用会话ID
    session_id = request.session_id or str(uuid.uuid4())

    # 获取上下文
    context = ""
    retrieved_docs = []
    source_info = []  # 新增：存储文档来源信息
    chat_metadata = {"mode": request.mode}

    # 优先处理指定的上下文 (无论何种模式)

    if request.context_type and request.context_id:
        from app.tools.data_tools import get_learning_content
        # 获取上下文内容（支持 chapter, section, subsection）
        content_summary = get_learning_content(db, request.context_type, request.context_id)
        
        if content_summary:
            context = content_summary
            retrieved_docs = [{"content": content_summary, "metadata": {"title": f"Specified {request.context_type} Context", "doc_type": request.context_type}}]
            source_info.append({
                'chapter_id': request.chapter_id,
                'title': f"{request.context_type} {request.context_id}",
                'doc_type': request.context_type
            })

    if request.mode == "quiz":
        # 如果是出题模式，直接构建强制性的JSON格式提示词

            if context:

                request.message = f"""你是一个专业的英语出题AI助手。请基于以下提供的上下文内容生成题目。

    

    **参考内容：**

    {context}

    

    **用户要求：**

    {request.message}

    

    **重要要求：**

    1. 你必须直接生成题目，不要调用任何工具

    2. 必须返回合法的JSON格式，不要包含任何其他文字说明

    3. JSON格式必须包含以下结构：

    {{

      "generate_interactive_quiz_response": {{

        "count": 题目数量,

        "questions": [

          {{

            "question": "题目内容",

            "quiz_type": "题目类型(choice/blank/translation/writing)",

            "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}},

            "correct_answer": "正确答案(如A或具体答案)",

            "explanation": "解析说明"

          }}

        ],

        "topic": "出题主题",

        "quiz_type": "mixed",

        "difficulty": "intermediate"

      }}

    }}

    

    4. 不要使用markdown代码块(如 ```json)

    5. 不要添加任何解释性文字

    6. 直接输出JSON字符串即可

    

    请根据用户要求生成题目并返回JSON格式。"""

            else:

                request.message = f"""你是一个专业的英语出题AI助手。

    

    **用户要求：**

    {request.message}

    

    **重要要求：**

    1. 你必须直接生成题目，不要调用任何工具

    2. 必须返回合法的JSON格式，不要包含任何其他文字说明

    3. JSON格式必须包含以下结构：

    {{

      "generate_interactive_quiz_response": {{

        "count": 题目数量,

        "questions": [

          {{

            "question": "题目内容",

            "quiz_type": "题目类型(choice/blank/translation/writing)",

            "options": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}},

            "correct_answer": "正确答案(如A或具体答案)",

            "explanation": "解析说明"

          }}

        ],

        "topic": "出题主题",

        "quiz_type": "mixed",

        "difficulty": "intermediate"

      }}

    }}

    

    4. 不要使用markdown代码块(如 ```json)

    5. 不要添加任何解释性文字

    6. 直接输出JSON字符串即可

    

    请根据用户要求生成题目并返回JSON格式。"""

    elif request.use_rag and request.message:
        # 如果没有指定上下文或未找到内容，则进行通用 RAG 检索
        if not context:
            # 使用RAG检索相关内容（不限制章节，搜索所有文档）
            results = rag_service.search(
                query=request.message,
                chapter_id=None,  # 不限制章节
                top_k=5  # 增加检索数量
            )

            if results:
                context = "\n\n---\n\n".join([r['content'] for r in results])
                retrieved_docs = results

                # 提取文档来源信息
                for r in results:
                    metadata = r.get('metadata', {})
                    source_info.append({
                        'chapter_id': metadata.get('chapter_id'),
                        'title': metadata.get('title'),
                        'doc_type': metadata.get('doc_type')
                    })

    # 获取聊天历史
    chat_history_records = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at.desc()).limit(5).all()

    # 构建聊天历史
    chat_history = []
    for record in reversed(chat_history_records):
        chat_history.append({"role": "user", "content": record.user_message})
        chat_history.append({"role": "assistant", "content": record.assistant_message})

    # 调用LLM
    if request.mode == "quiz":
        # 出题模式：使用简单的chat方法，避免工具调用
        system_prompt = """你是一个专业的英语出题AI助手。你必须严格遵循用户的要求生成题目，并返回JSON格式。

关键要求：
1. 必须返回合法的JSON格式，不要包含任何其他文字说明
2. 不要使用markdown代码块(如 ```json)
3. 不要添加任何解释性文字
4. 直接输出JSON字符串即可"""

        messages = [{"role": "system", "content": system_prompt}]
        # 添加聊天历史（但限制数量以避免token过多）
        if chat_history:
            # 只取最近2轮对话
            recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
            messages.extend(recent_history)
        # 添加当前问题
        messages.append({"role": "user", "content": request.message})

        # 使用简单的chat方法
        assistant_message = llm_service.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=3000
        )
    else:
        # 聊天模式：使用answer_question方法（支持工具调用）
        assistant_message = llm_service.answer_question(
            db=db,  # 传递数据库会话
            question=request.message,
            context=context if context else None,
            source_info=source_info if source_info else None,  # 传递来源信息
            chat_history=chat_history,
            image=request.image,  # 传递图片
            student_id=current_user.id  # 传递学生ID
        )

    # 保存聊天记录
    chat_record = ChatHistory(
        user_id=current_user.id,
        chapter_id=request.chapter_id,
        session_id=session_id,
        user_message=request.message,
        assistant_message=assistant_message,
        retrieved_docs=json.dumps(retrieved_docs, ensure_ascii=False) if retrieved_docs else None,
        doc_count=len(retrieved_docs),
        chat_metadata=json.dumps(chat_metadata, ensure_ascii=False)
    )

    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)
    
    # 转换为响应模型需要的格式
    response_dict = chat_record.to_dict()
    # 手动处理 chat_metadata，确保它是字典
    if chat_record.chat_metadata:
        try:
            response_dict['chat_metadata'] = json.loads(chat_record.chat_metadata)
        except:
            response_dict['chat_metadata'] = {}
    else:
        response_dict['chat_metadata'] = {}
            
    return response_dict


from app.models.quiz import QuizRecord
from app.models.custom_quiz import CustomQuizRecord
from app.models.wrong_question import WrongQuestion
import logging

logger = logging.getLogger(__name__)

@router.post("/quiz/submit/{message_id}", response_model=Dict[str, Any])
def submit_quiz_result(
    message_id: int,
    submission: QuizSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    提交测验结果，并同步保存到 CustomQuizRecord (出题模式专用)
    """
    chat_record = db.query(ChatHistory).filter(
        ChatHistory.id == message_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not chat_record:
        raise HTTPException(status_code=404, detail="Quiz record not found")
        
    # 1. 更新 ChatHistory metadata (作为备份)
    metadata = {}
    if chat_record.chat_metadata:
        try:
            metadata = json.loads(chat_record.chat_metadata)
        except:
            metadata = {}
            
    metadata['user_answers'] = submission.user_answers
    metadata['score'] = submission.score
    metadata['is_correct'] = submission.is_correct
    metadata['submitted_at'] = datetime.utcnow().isoformat()
    
    chat_record.chat_metadata = json.dumps(metadata, ensure_ascii=False)
    
    # 2. 保存到 CustomQuizRecord (独立的出题模式练习表)
    try:
        # 解析题目数据
        quiz_data = None
        assistant_msg = chat_record.assistant_message
        
        # 尝试从 assistant_message 提取 JSON
        try:
            # 清理可能的 markdown
            clean_msg = assistant_msg.replace('```json', '').replace('```', '').strip()
            parsed = json.loads(clean_msg)
            
            if "generate_interactive_quiz_response" in parsed:
                quiz_data = parsed["generate_interactive_quiz_response"]
            elif "questions" in parsed:
                quiz_data = parsed
            
        except json.JSONDecodeError:
             # 尝试正则提取
            import re
            match = re.search(r'\{[\s\S]*"generate_interactive_quiz_response"[\s\S]*\}', assistant_msg)
            if match:
                 try:
                     parsed = json.loads(match.group(0))
                     quiz_data = parsed.get("generate_interactive_quiz_response")
                 except:
                     pass
        
        # 如果还是没找到，尝试最宽松的提取：找第一个包含 questions 的 JSON 对象
        if not quiz_data:
             import re
             match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', assistant_msg)
             if match:
                 try:
                     parsed = json.loads(match.group(0))
                     quiz_data = parsed
                 except:
                     pass

        if quiz_data and "questions" in quiz_data:
            questions = quiz_data["questions"]
            
            # 创建 CustomQuizRecord
            custom_record = CustomQuizRecord(
                user_id=current_user.id,
                chat_history_id=chat_record.id,
                chapter_id=chat_record.chapter_id,
                topic=quiz_data.get("topic", "AI生成练习"),
                quiz_type=quiz_data.get("quiz_type", "mixed"),
                difficulty=quiz_data.get("difficulty", "intermediate"),
                question_count=len(questions),
                questions_data=json.dumps(questions, ensure_ascii=False),
                user_answers=json.dumps(submission.user_answers, ensure_ascii=False),
                results_data=json.dumps({
                    "score": submission.score,
                    "is_correct": submission.is_correct
                }, ensure_ascii=False),
                score=submission.score,
                is_completed=True,
                completed_at=datetime.utcnow()
            )
            db.add(custom_record)
            
            logger.info(f"Saved CustomQuizRecord for user {current_user.id} from ChatHistory {message_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync CustomQuizRecord: {e}", exc_info=True)
        # 不阻断主流程，因为metadata已经保存了
    
    db.commit()
    
    return {"status": "success", "message_id": message_id}




@router.get("/quiz/history", response_model=List[Dict[str, Any]])
def get_quiz_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取出题历史 (合并 CustomQuizRecord 和 ChatHistory)
    """
    result = []
    
    # 1. 获取已完成/提交的练习 (CustomQuizRecord)
    custom_records = db.query(CustomQuizRecord).filter(
        CustomQuizRecord.user_id == current_user.id
    ).order_by(CustomQuizRecord.created_at.desc()).limit(limit).all()
    
    existing_chat_ids = set()
    
    if custom_records:
        for record in custom_records:
            result.append(record.to_dict())
            if record.chat_history_id:
                existing_chat_ids.add(record.chat_history_id)
                
    # 2. 获取未提交/生成中的练习 (ChatHistory)
    # 排除掉已经存在于 custom_records 中的记录 (通过 chat_history_id 关联)
    chat_records = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.assistant_message.like('%"generate_interactive_quiz_response"%'),
        ChatHistory.id.notin_(existing_chat_ids) # 排除已提交的
    ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
    
    for record in chat_records:
        # 尝试构造兼容的格式
        record_dict = record.to_dict()
        if record.chat_metadata:
            try:
                metadata = json.loads(record.chat_metadata)
            except:
                metadata = {}
        else:
             metadata = {}
        
        # 适配前端需要的结构
        # 注意：这里我们构造一个类似于 CustomQuizRecord 的结构，但标记为未完成
        
        # 尝试解析题目以获取 topic 等信息 (可选)
        topic = record.user_message
        
        adapter_dict = {
            "id": record.id, # 使用 chat_history id
            "chat_history_id": record.id, # 明确标记
            "created_at": record_dict["created_at"],
            "topic": topic,
            "score": metadata.get('score', 0),
            "is_completed": bool(metadata.get('user_answers')), # 通常是 False
            "questions": [], # 前端会根据 questions 是否为空来决定是否使用旧版解析逻辑，或者我们在这里预解析
            "assistant_message": record.assistant_message, # 保留原始消息供前端解析
            "quiz_type": "mixed" # 默认
        }
        result.append(adapter_dict)
    
    # 重新按时间排序
    result.sort(key=lambda x: x['created_at'], reverse=True)
    
    return result[:limit]



@router.get("/history/{session_id}", response_model=List[ChatResponse])
def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取聊天历史

    - **session_id**: 会话ID
    - **limit**: 返回数量限制（默认50）
    """
    records = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at).limit(limit).all()

    result = []
    for record in records:
        record_dict = record.to_dict()
        if record.chat_metadata:
            try:
                record_dict['chat_metadata'] = json.loads(record.chat_metadata)
            except:
                record_dict['chat_metadata'] = {}
        else:
             record_dict['chat_metadata'] = {}
        result.append(record_dict)
        
    return result



@router.get("/sessions", response_model=List[dict])
def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户的所有会话列表
    """
    from sqlalchemy import func, distinct

    # 获取所有不同的session_id及其最新消息时间
    sessions = db.query(
        ChatHistory.session_id,
        ChatHistory.chapter_id,
        func.max(ChatHistory.created_at).label('last_message_at'),
        func.count(ChatHistory.id).label('message_count')
    ).filter(
        ChatHistory.user_id == current_user.id
    ).group_by(
        ChatHistory.session_id,
        ChatHistory.chapter_id
    ).order_by(
        func.max(ChatHistory.created_at).desc()
    ).limit(20).all()

    # 格式化结果
    result = []
    for session in sessions:
        # 获取该会话的第一条消息作为预览
        first_message = db.query(ChatHistory).filter(
            ChatHistory.session_id == session.session_id,
            ChatHistory.user_id == current_user.id
        ).order_by(ChatHistory.created_at).first()

        result.append({
            "session_id": session.session_id,
            "chapter_id": session.chapter_id,
            "last_message_at": session.last_message_at,
            "message_count": session.message_count,
            "preview": first_message.user_message[:50] + "..." if first_message and len(first_message.user_message) > 50 else first_message.user_message if first_message else ""
        })

    return result


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除聊天会话
    """
    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.session_id == session_id
    ).delete()

    db.commit()

    return None
