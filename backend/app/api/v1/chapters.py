"""
章节相关API路由
"""

from typing import List, Optional
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas.chapter import ChapterCreate, ChapterUpdate, ChapterResponse
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.user import User
from app.api.dependencies import get_db, get_current_active_user, require_teacher
from app.services.course_parser import CourseParserService
import json

router = APIRouter(prefix="/chapters", tags=["章节管理"])


@router.get("/", response_model=List[ChapterResponse])
def get_chapters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取章节列表

    - **skip**: 跳过数量（分页）
    - **limit**: 返回数量限制
    """
    chapters = db.query(Chapter).order_by(Chapter.chapter_number).offset(skip).limit(limit).all()
    return chapters


@router.get("/{chapter_id}", response_model=ChapterResponse)
def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个章节详情
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    return chapter


@router.post("/", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
def create_chapter(
    chapter_data: ChapterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    创建章节（仅教师）

    - **chapter_number**: 章节编号
    - **title**: 章节标题
    - **description**: 章节描述（可选）
    - **learning_objectives**: 学习目标列表（可选）
    - **key_points**: 知识点列表（可选）
    """
    # 检查章节编号是否已存在
    existing = db.query(Chapter).filter(Chapter.chapter_number == chapter_data.chapter_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="章节编号已存在"
        )

    # 创建章节
    chapter = Chapter(
        chapter_number=chapter_data.chapter_number,
        title=chapter_data.title,
        description=chapter_data.description,
        learning_objectives=json.dumps(chapter_data.learning_objectives, ensure_ascii=False) if chapter_data.learning_objectives else None,
        key_points=json.dumps(chapter_data.key_points, ensure_ascii=False) if chapter_data.key_points else None,
        word_count=chapter_data.word_count or 0,
        difficulty_level=chapter_data.difficulty_level or "intermediate"
    )

    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    return chapter


@router.put("/{chapter_id}", response_model=ChapterResponse)
def update_chapter(
    chapter_id: int,
    chapter_data: ChapterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    更新章节（仅教师）
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )

    # 更新字段
    update_data = chapter_data.dict(exclude_unset=True)
    if 'learning_objectives' in update_data and update_data['learning_objectives']:
        update_data['learning_objectives'] = json.dumps(update_data['learning_objectives'], ensure_ascii=False)
    if 'key_points' in update_data and update_data['key_points']:
        update_data['key_points'] = json.dumps(update_data['key_points'], ensure_ascii=False)

    for key, value in update_data.items():
        setattr(chapter, key, value)

    db.commit()
    db.refresh(chapter)

    return chapter


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    删除章节（仅教师）
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )

    # Delete vectors first
    try:
        from app.services.rag_service import rag_service
        rag_service.delete_chapter_vectors(chapter_id)
    except Exception as e:
        print(f"Warning: Failed to delete vectors for chapter {chapter_id}: {e}")

    db.delete(chapter)
    db.commit()

    return None


@router.get("/{chapter_id}/export")
def export_chapter(
    chapter_id: int,
    format: str = "md",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    导出章节内容 (默认/仅支持 Markdown)
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
        
    if format != "md":
        raise HTTPException(status_code=400, detail="目前仅支持导出为 Markdown (md) 格式")
        
    # Construct Markdown content
    content = f"# {chapter.title}\n\n"
    if chapter.description:
        content += f"- **章节目标**: {chapter.description}\n\n"
        
    # Sort sections
    sections = sorted(chapter.sections, key=lambda s: (s.order if s.order is not None else 0, s.id))
    
    for section in sections:
        content += f"## {section.title}\n\n"
        if section.description:
            content += f"{section.description}\n\n"
            
        subsections = sorted(section.subsections, key=lambda s: (s.order if s.order is not None else 0, s.id))
        for sub in subsections:
            content += f"### {sub.title}\n\n"
            
            # Metadata as bullet points
            content += f"- 权重: {sub.weight}\n"
            content += f"- 合格分数: {sub.passing_score}\n"
            if sub.min_questions:
                 content += f"- 最少题数: {sub.min_questions}\n"
            content += "\n"
            
            if sub.content:
                # If content is multiline, ensure it renders well. 
                # Assuming content is text.
                content += f"{sub.content}\n\n"
                
            if sub.requirements:
                 content += "**要求**:\n\n"
                 req_text = str(sub.requirements)
                 try:
                     parsed = json.loads(req_text)
                     
                     # Map keys to user-friendly labels
                     key_map = {
                         "types": "题型",
                         "type": "题型",
                         "count": "题量",
                         "focus": "考察重点",
                         "description": "说明",
                         "tags": "标签",
                         "knowledge_points": "知识点"
                     }
                     
                     # Order of keys to display
                     ordered_keys = ["types", "count", "focus", "description"]
                     # Add remaining keys
                     for k in parsed.keys():
                         if k not in ordered_keys and k != "difficulty":
                             ordered_keys.append(k)
                             
                     for key in ordered_keys:
                         if key not in parsed:
                             continue
                             
                         # Skip difficulty as per user request
                         if key == "difficulty":
                             continue
                             
                         value = parsed[key]
                         label = key_map.get(key, key)
                         
                         if isinstance(value, list):
                             val_str = "、".join(map(str, value))
                             content += f"- {label}: {val_str}\n"
                         elif isinstance(value, dict):
                             content += f"- {label}:\n"
                             for sub_k, sub_v in value.items():
                                 content += f"  - {sub_k}: {sub_v}\n"
                         else:
                             # Translate common values if needed (e.g., difficulty)
                             if key == "difficulty":
                                 diff_map = {"easy": "简单", "medium": "中等", "hard": "困难"}
                                 value = diff_map.get(str(value).lower(), value)
                                 
                             content += f"- {label}: {value}\n"
                     
                     content += "\n"
                 except:
                     content += f"{req_text}\n\n"
                     
    # Save to temp
    temp_dir = tempfile.gettempdir()
    # Sanitize filename
    safe_title = "".join([c for c in chapter.title if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_title:
        safe_title = f"chapter_{chapter_id}"
        
    filename = f"{safe_title}.md"
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return FileResponse(
        file_path, 
        filename=filename,
        media_type="text/markdown"
    )




@router.post("/structure/upload")
async def upload_course_structure(
    chapter_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """
    上传课程结构文档 (支持 Markdown, Word, PDF)
    - **chapter_id**: 可选。如果提供，将替换该章节的内容。
    """
    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if ext not in ['md', 'docx', 'pdf', 'txt']:
        raise HTTPException(status_code=400, detail="Only Markdown, Word, and PDF files are supported")
    
    # Handle replacement logic if chapter_id provided
    if chapter_id:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="指定替换的章节不存在")
            
        # 1. Clean up vectors
        try:
            from app.services.rag_service import rag_service
            rag_service.delete_chapter_vectors(chapter_id)
        except Exception as e:
            print(f"Warning: Failed to delete vectors for chapter {chapter_id}: {e}")
            
        # 2. Delete existing sections (which cascades to subsections)
        # We manually delete sections to ensure clean state
        for section in chapter.sections:
            db.delete(section)
        db.commit()
        db.refresh(chapter)

    content = await file.read()
    
    parser = CourseParserService(db)
    try:
        # 1. Extract text
        raw_text = parser.extract_text_from_file(content, file.filename)
        
        # 2. Parse with AI if it's a binary document (docx/pdf) or unstructured text
        # If the text already contains markers like [章节], skip AI parsing
        if "[章节]" in raw_text or "[节]" in raw_text:
            structure_content = raw_text
            print("Detected structured content, skipping AI parsing")
        elif ext in ['docx', 'pdf', 'txt']:
            # For txt, we could check if it looks like our markdown structure, but for now let's use AI 
            # if user expects AI structure recognition.
            structure_content = parser.parse_unstructured_content(raw_text)
        else:
            structure_content = raw_text
            
        # 3. Create structure
        chapter = parser.parse_with_strict_rules(structure_content, target_chapter_id=chapter_id)
        
        # 4. Vectorize
        vector_count = 0
        if chapter:
            try:
                from app.services.rag_service import rag_service
                db.refresh(chapter)
                for section in chapter.sections:
                    for subsection in section.subsections:
                        rag_service.vectorize_subsection(db, subsection.id)
                        vector_count += 1
            except Exception as e:
                print(f"Warning: Failed to vectorize chapter {chapter.id}: {e}")
                
        return {"message": "Structure created successfully", "chapter_id": chapter.id if chapter else None, "vectorized_subsections": vector_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")
