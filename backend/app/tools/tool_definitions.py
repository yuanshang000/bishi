TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_wrong_questions_by_subsection",
            "description": "获取指定小目标（subsection）的错题记录，用于分析痛点和针对性出题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    },
                    "subsection_id": {
                        "type": "integer",
                        "description": "小目标ID (subsection ID)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回错题数量限制，默认为5"
                    }
                },
                "required": ["student_id", "subsection_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_learning_progress",
            "description": "获取学生当前的学习进度，包括正在学习的章节和小节信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_content",
            "description": "根据当前完成的小目标ID，获取下一阶段的学习内容（下一小目标、下一节或下一章）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_subsection_id": {
                        "type": "integer",
                        "description": "当前刚完成或正在进行的小目标ID"
                    }
                },
                "required": ["current_subsection_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_weak_points",
            "description": "分析学生的薄弱点，返回平均分最低的几个领域及相关错题统计。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    }
                },
                "required": ["student_id"]
            }
        }
    }
]
