-- 删除并重新创建 quiz_records 表
-- 2026-01-12

USE college_english_assistant;

-- 删除旧表
DROP TABLE IF EXISTS quiz_records;

-- 重新创建表（包含 practice_mode 字段）
CREATE TABLE quiz_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    chapter_id INT NULL COMMENT '章节ID（随机练习和综合练习可为空）',
    practice_mode VARCHAR(20) NOT NULL DEFAULT 'chapter' COMMENT '练习方式（chapter=章节练习, random=随机练习, comprehensive=综合练习）',
    quiz_type VARCHAR(50) NOT NULL COMMENT '练习类型（listening/reading/translation/writing等）',
    question_count INT DEFAULT 0 COMMENT '题目总数',
    questions TEXT COMMENT '题目列表（JSON格式）',
    user_answers TEXT COMMENT '用户答案（JSON格式）',
    correct_answers TEXT COMMENT '正确答案（JSON格式）',
    results TEXT COMMENT '详细批改结果（JSON格式，包含每道题的反馈）',
    score FLOAT DEFAULT 0.0 COMMENT '得分',
    accuracy FLOAT DEFAULT 0.0 COMMENT '正确率（0-100）',
    time_spent INT DEFAULT 0 COMMENT '用时（秒）',
    knowledge_point_ids TEXT COMMENT '关联的知识点ID列表（JSON数组）',
    is_completed TINYINT DEFAULT 0 COMMENT '是否完成（1=是，0=否）',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_chapter_id (chapter_id),
    INDEX idx_practice_mode (practice_mode),
    INDEX idx_quiz_type (quiz_type),
    INDEX idx_created_at (created_at),

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='练习记录表';

-- 显示新表结构
DESCRIBE quiz_records;

SELECT 'quiz_records table recreated successfully!' AS message;
