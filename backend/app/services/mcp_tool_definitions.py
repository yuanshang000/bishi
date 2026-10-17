"""
MCP 工具定义
用于 MCP 模式的工具定义
"""

MCP_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_student_quiz_history",
            "description": "获取学生最近的测验历史记录，包括分数、涉及的章节等信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回记录数量限制，默认为5"
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_course_content",
            "description": "从课程内容的向量数据库中检索相关知识。可以根据关键词或指定章节进行搜索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或问题描述"
                    },
                    "chapter_id": {
                        "type": "integer",
                        "description": "指定章节ID进行过滤（可选）"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量（可选，默认3）"
                    }
                },
                "required": ["query"]
            }
        }
    },
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
