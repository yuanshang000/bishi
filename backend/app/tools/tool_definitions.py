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
            "description": "获取学生下一阶段的学习内容。如果只提供student_id，会自动查找最新进度并推荐。",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_subsection_id": {
                        "type": "integer",
                        "description": "当前刚完成的小目标ID (可选)"
                    },
                    "student_id": {
                        "type": "integer",
                        "description": "学生ID (推荐使用)"
                    }
                },
                "required": []
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
    },
    {
        "type": "function",
        "function": {
            "name": "generate_interactive_quiz",
            "description": "Generate interactive quiz based on user topic/prompt. Use this when user explicitly asks to generate a quiz or is in Quiz Mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "User's topic or prompt for the quiz."
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of questions to generate (default: 3)."
                    },
                    "quiz_type": {
                        "type": "string",
                        "description": "Type of quiz (mixed, choice, blank, etc.) (default: mixed)."
                    },
                    "difficulty": {
                        "type": "string",
                        "description": "Difficulty level (easy, intermediate, hard) (default: intermediate)."
                    },
                    "student_id": {
                        "type": "integer",
                        "description": "Student ID."
                    }
                },
                "required": ["topic"]
            }
        }
    }
]
