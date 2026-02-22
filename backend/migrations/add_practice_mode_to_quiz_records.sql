-- 添加 practice_mode 字段到 quiz_records 表
-- 2026-01-12

-- 添加 practice_mode 字段
ALTER TABLE quiz_records
ADD COLUMN practice_mode VARCHAR(20) NOT NULL DEFAULT 'chapter' COMMENT '练习方式（chapter=章节练习, random=随机练习, comprehensive=综合练习）'
AFTER chapter_id;

-- 添加索引以提高查询性能
CREATE INDEX idx_practice_mode ON quiz_records(practice_mode);

-- 将 chapter_id 改为可空（因为随机练习和综合练习不需要章节）
ALTER TABLE quiz_records
MODIFY COLUMN chapter_id INT NULL COMMENT '章节ID';

-- 更新现有数据，将 NULL practice_mode 设置为 'chapter'
UPDATE quiz_records
SET practice_mode = 'chapter'
WHERE practice_mode IS NULL OR practice_mode = '';
