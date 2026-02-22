-- 修改 content 字段为 LONGTEXT 类型以支持大文件
-- LONGTEXT 可以存储最多 4GB 的文本数据

ALTER TABLE course_documents MODIFY COLUMN content LONGTEXT NULL COMMENT '文档内容';
