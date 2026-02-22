-- ============================================================
-- 大学英语助手系统 - 完整数据库初始化脚本
-- 创建日期：2026-01-12
-- ============================================================

USE college_english_assistant;

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================================
-- 1. 用户表 (users)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（唯一）',
    email VARCHAR(100) UNIQUE COMMENT '电子邮箱',
    full_name VARCHAR(100) COMMENT '真实姓名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    role VARCHAR(20) NOT NULL DEFAULT 'student' COMMENT '用户角色（teacher/student）',
    is_active INT DEFAULT 1 COMMENT '账号状态（1=启用，0=禁用）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. 章节表 (chapters)
-- ============================================================
CREATE TABLE IF NOT EXISTS chapters (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '章节ID',
    chapter_number INT NOT NULL UNIQUE COMMENT '章节编号（唯一）',
    title VARCHAR(200) NOT NULL COMMENT '章节标题',
    description TEXT COMMENT '章节描述',
    learning_objectives TEXT COMMENT '学习目标（JSON格式）',
    key_points TEXT COMMENT '知识点列表（JSON格式）',
    word_count INT DEFAULT 0 COMMENT '词汇量',
    difficulty_level VARCHAR(20) DEFAULT 'intermediate' COMMENT '难度等级',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_chapter_number (chapter_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='章节表';

-- ============================================================
-- 3. 课程文档表 (course_documents)
-- ============================================================
CREATE TABLE IF NOT EXISTS course_documents (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
    chapter_id INT NOT NULL COMMENT '所属章节ID',
    title VARCHAR(200) NOT NULL COMMENT '文档标题',
    doc_type VARCHAR(50) NOT NULL COMMENT '文档类型（textbook/teaching_plan/exercise/reference/knowledge）',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_name VARCHAR(200) COMMENT '原始文件名',
    file_size INT DEFAULT 0 COMMENT '文件大小（字节）',
    content LONGTEXT COMMENT '文档文本内容',
    content_hash VARCHAR(64) COMMENT '内容哈希（用于去重）',
    is_vectorized INT DEFAULT 0 COMMENT '是否已向量化（1=是，0=否）',
    vector_count INT DEFAULT 0 COMMENT '向量数量',
    chroma_ids TEXT COMMENT 'ChromaDB中的ID列表（JSON格式）',
    knowledge_points TEXT COMMENT '提取的知识点列表（JSON格式）',
    knowledge_tags TEXT COMMENT '知识点标签（JSON数组）',
    doc_metadata TEXT COMMENT '其他元数据（JSON格式）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_chapter_id (chapter_id),
    INDEX idx_doc_type (doc_type),
    INDEX idx_content_hash (content_hash),

    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程文档表';

-- ============================================================
-- 4. 练习记录表 (quiz_records) - 包含新的 practice_mode 字段
-- ============================================================
CREATE TABLE IF NOT EXISTS quiz_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    chapter_id INT NULL COMMENT '章节ID（随机练习和综合练习可为空）',
    practice_mode VARCHAR(20) NOT NULL DEFAULT 'chapter' COMMENT '练习方式（chapter=章节练习, random=随机练习, comprehensive=综合练习）',
    quiz_type VARCHAR(50) NOT NULL COMMENT '练习类型（listening/reading/translation/writing等）',
    question_count INT DEFAULT 0 COMMENT '题目总数',
    questions TEXT COMMENT '题目列表（JSON格式）',
    user_answers TEXT COMMENT '用户答案（JSON格式）',
    correct_answers TEXT COMMENT '正确答案（JSON格式）',
    results TEXT COMMENT '详细批改结果（JSON格式）',
    score FLOAT DEFAULT 0.0 COMMENT '得分',
    accuracy FLOAT DEFAULT 0.0 COMMENT '正确率（0-100）',
    time_spent INT DEFAULT 0 COMMENT '用时（秒）',
    knowledge_point_ids TEXT COMMENT '关联知识点ID列表（JSON数组）',
    is_completed TINYINT DEFAULT 0 COMMENT '是否完成（1=是，0=否）',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_user_id (user_id),
    INDEX idx_chapter_id (chapter_id),
    INDEX idx_practice_mode (practice_mode),
    INDEX idx_quiz_type (quiz_type),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='练习记录表';

-- ============================================================
-- 5. 聊天历史表 (chat_histories)
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_histories (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    chapter_id INT COMMENT '关联章节ID（可选）',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    user_message TEXT NOT NULL COMMENT '用户消息',
    assistant_message TEXT NOT NULL COMMENT '助手回复',
    message_role VARCHAR(20) DEFAULT 'user' COMMENT '消息角色（user/assistant）',
    retrieved_docs TEXT COMMENT '检索到的文档片段（JSON格式）',
    doc_count INT DEFAULT 0 COMMENT '检索文档数量',
    chat_metadata TEXT COMMENT '其他元数据（JSON格式）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_user_id (user_id),
    INDEX idx_chapter_id (chapter_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天历史表';

-- ============================================================
-- 6. 错题表 (wrong_questions)
-- ============================================================
CREATE TABLE IF NOT EXISTS wrong_questions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '错题ID',
    user_id INT NOT NULL COMMENT '用户ID',
    quiz_record_id INT NOT NULL COMMENT '练习记录ID',
    chapter_id INT NOT NULL COMMENT '章节ID',
    question_type VARCHAR(50) NOT NULL COMMENT '题目类型',
    question_data TEXT NOT NULL COMMENT '题目内容（JSON格式）',
    user_answer TEXT COMMENT '用户答案',
    correct_answer TEXT COMMENT '正确答案',
    score FLOAT DEFAULT 0.0 COMMENT '得分（0-1）',
    knowledge_point_ids TEXT COMMENT '关联知识点ID（JSON数组）',
    is_mastered INT DEFAULT 0 COMMENT '是否已掌握（1=是，0=否）',
    retry_count INT DEFAULT 0 COMMENT '重做次数',
    last_retry_score FLOAT COMMENT '最后一次重做得分',
    last_retry_at DATETIME COMMENT '最后重做时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_user_id (user_id),
    INDEX idx_quiz_record_id (quiz_record_id),
    INDEX idx_chapter_id (chapter_id),
    INDEX idx_question_type (question_type),
    INDEX idx_user_chapter (user_id, chapter_id),
    INDEX idx_user_mastered (user_id, is_mastered),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_record_id) REFERENCES quiz_records(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错题表';

-- ============================================================
-- 完成提示
-- ============================================================
SELECT '============================================================' AS '';
SELECT '数据库初始化完成！' AS '状态';
SELECT '============================================================' AS '';
SELECT '已创建的表：' AS '';
SELECT '1. users - 用户表' AS '';
SELECT '2. chapters - 章节表' AS '';
SELECT '3. course_documents - 课程文档表' AS '';
SELECT '4. quiz_records - 练习记录表（包含practice_mode字段）' AS '';
SELECT '5. chat_histories - 聊天历史表' AS '';
SELECT '6. wrong_questions - 错题表' AS '';
SELECT '============================================================' AS '';

-- 显示所有表
SHOW TABLES;
