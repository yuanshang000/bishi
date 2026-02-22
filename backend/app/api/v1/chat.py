"""
问答相关API路由
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import json

from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage
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
    """
    # 生成或使用会话ID
    session_id = request.session_id or str(uuid.uuid4())

    # 获取上下文
    context = ""
    retrieved_docs = []
    source_info = []  # 新增：存储文档来源信息

    # 优先处理指定的上下文 (无论何种模式)
    if request.context_type == "subsection" and request.context_id:
        from app.tools.data_tools import _get_subsection_content_summary
        # 获取小节内容的详细摘要（包含 DB 文本、KnowledgePoint 和 RAG 检索）
        content_summary = _get_subsection_content_summary(db, request.context_id)
        if content_summary:
            context = content_summary
            retrieved_docs = [{"content": content_summary, "metadata": {"title": "Specified Subsection Context", "doc_type": "subsection"}}]
            source_info.append({
                'chapter_id': request.chapter_id,
                'title': f"Subsection {request.context_id}",
                'doc_type': 'subsection'
            })

    if request.mode == "quiz":
        # 如果是出题模式，添加系统指令
        # 即使是出题模式，如果获取到了 context，也应该包含在内
        base_instruction = "(系统指令: 用户正在出题模式下，请调用 generate_interactive_quiz 工具生成题目，并以 标签返回结果)"
        if context:
            request.message = f"{base_instruction} 请基于以下提供的上下文内容进行出题：\n\n{context}\n\n用户的出题提示词: {request.message}"
        else:
            request.message = f"{base_instruction} 用户的出题提示词: {request.message}"
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
        doc_count=len(retrieved_docs)
    )

    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    return chat_record


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

    return records


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
