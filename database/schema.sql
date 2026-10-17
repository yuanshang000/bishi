
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`version_num`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chapters` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '章节ID',
  `chapter_number` int NOT NULL COMMENT '章节编号（唯一）',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '章节标题',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '章节描述',
  `learning_objectives` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '学习目标（JSON格式）',
  `key_points` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '知识点列表（JSON格式）',
  `word_count` int DEFAULT NULL COMMENT '词汇量',
  `difficulty_level` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '难度等级',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `ix_chapters_chapter_number` (`chapter_number`) USING BTREE,
  KEY `ix_chapters_id` (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_histories` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `chapter_id` int DEFAULT NULL COMMENT '关联章节ID（可选）',
  `session_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '会话ID（用于关联同一次对话）',
  `user_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户消息',
  `assistant_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '助手回复',
  `message_role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '消息角色（user/assistant）',
  `retrieved_docs` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '检索到的文档片段（JSON格式）',
  `doc_count` int DEFAULT NULL COMMENT '检索文档数量',
  `chat_metadata` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '其他元数据（JSON格式）',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_chat_histories_id` (`id`) USING BTREE,
  KEY `ix_chat_histories_session_id` (`session_id`) USING BTREE,
  KEY `ix_chat_histories_user_id` (`user_id`) USING BTREE,
  KEY `ix_chat_histories_chapter_id` (`chapter_id`) USING BTREE,
  KEY `ix_chat_histories_created_at` (`created_at`) USING BTREE,
  CONSTRAINT `chat_histories_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `chat_histories_ibfk_2` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=239 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_documents` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '文档ID',
  `chapter_id` int NOT NULL COMMENT '所属章节ID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '文档标题',
  `doc_type` enum('textbook','teaching_plan','exercise','reference','knowledge') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '文档类型',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '文件路径',
  `file_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '原始文件名',
  `file_size` int DEFAULT NULL COMMENT '文件大小（字节）',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '文档文本内容（支持大文件）',
  `content_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '内容哈希（用于去重）',
  `is_vectorized` int DEFAULT NULL COMMENT '是否已向量化（1=是，0=否）',
  `vector_count` int DEFAULT NULL COMMENT '向量数量',
  `chroma_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT 'ChromaDB中的ID列表（JSON格式）',
  `knowledge_points` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '提取的知识点列表（JSON格式）',
  `knowledge_tags` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '知识点标签（JSON数组）',
  `doc_metadata` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '其他元数据（JSON格式）',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_course_documents_chapter_id` (`chapter_id`) USING BTREE,
  KEY `ix_course_documents_doc_type` (`doc_type`) USING BTREE,
  KEY `ix_course_documents_id` (`id`) USING BTREE,
  KEY `ix_course_documents_content_hash` (`content_hash`) USING BTREE,
  CONSTRAINT `course_documents_ibfk_1` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `custom_quiz_records` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `chat_history_id` int DEFAULT NULL COMMENT '关联的聊天记录ID',
  `chapter_id` int DEFAULT NULL COMMENT '关联章节ID',
  `topic` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '出题主题/提示词',
  `quiz_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '题目类型(choice/blank/translation/mixed)',
  `difficulty` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '难度',
  `question_count` int DEFAULT NULL COMMENT '题目数量',
  `questions_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '题目数据JSON',
  `user_answers` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '用户答案JSON',
  `results_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '判题结果JSON',
  `score` float DEFAULT NULL COMMENT '得分',
  `is_completed` tinyint(1) DEFAULT NULL COMMENT '是否完成',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `completed_at` datetime DEFAULT NULL COMMENT '完成时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_custom_quiz_records_user_id` (`user_id`) USING BTREE,
  KEY `ix_custom_quiz_records_chat_history_id` (`chat_history_id`) USING BTREE,
  KEY `ix_custom_quiz_records_chapter_id` (`chapter_id`) USING BTREE,
  KEY `ix_custom_quiz_records_id` (`id`) USING BTREE,
  CONSTRAINT `custom_quiz_records_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `custom_quiz_records_ibfk_2` FOREIGN KEY (`chat_history_id`) REFERENCES `chat_histories` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `custom_quiz_records_ibfk_3` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `knowledge_points` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subsection_id` int NOT NULL,
  `content` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '知识点内容(单词/短语/语法点)',
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '类型: word, grammar, phrase, other',
  `priority_score` float DEFAULT NULL COMMENT '优先级分数，越小优先级越高',
  `consecutive_errors` int DEFAULT NULL COMMENT '连续做错次数',
  `last_reviewed_at` datetime DEFAULT NULL COMMENT '上次复习时间',
  `total_attempts` int DEFAULT NULL COMMENT '总练习次数',
  `correct_attempts` int DEFAULT NULL COMMENT '做对次数',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_knowledge_points_subsection_id` (`subsection_id`) USING BTREE,
  KEY `ix_knowledge_points_id` (`id`) USING BTREE,
  CONSTRAINT `knowledge_points_ibfk_1` FOREIGN KEY (`subsection_id`) REFERENCES `subsections` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2013 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quiz_records` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `chapter_id` int DEFAULT NULL COMMENT '章节ID',
  `subsection_id` int DEFAULT NULL COMMENT '小目标ID',
  `practice_mode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '练习方式（chapter=章节练习, random=随机练习, comprehensive=综合练习）',
  `quiz_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '练习类型（choice/blank/translation等）',
  `difficulty` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '难度等级（low=低, medium=中/四级, high=高/六级）',
  `question_count` int DEFAULT NULL COMMENT '题目总数',
  `questions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '题目列表（JSON格式）',
  `user_answers` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '用户答案（JSON格式）',
  `correct_answers` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '正确答案（JSON格式）',
  `results` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '详细批改结果（JSON格式，包含每道题的反馈）',
  `score` float DEFAULT NULL COMMENT '得分',
  `accuracy` float DEFAULT NULL COMMENT '正确率（0-100）',
  `time_spent` int DEFAULT NULL COMMENT '用时（秒）',
  `knowledge_point_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '关联的知识点ID列表（JSON数组）',
  `is_completed` int DEFAULT NULL COMMENT '是否完成（1=是，0=否）',
  `started_at` datetime DEFAULT NULL COMMENT '开始时间',
  `completed_at` datetime DEFAULT NULL COMMENT '完成时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `section_id` int DEFAULT NULL COMMENT '节ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_quiz_records_id` (`id`) USING BTREE,
  KEY `ix_quiz_records_subsection_id` (`subsection_id`) USING BTREE,
  KEY `ix_quiz_records_quiz_type` (`quiz_type`) USING BTREE,
  KEY `ix_quiz_records_user_id` (`user_id`) USING BTREE,
  KEY `ix_quiz_records_practice_mode` (`practice_mode`) USING BTREE,
  KEY `ix_quiz_records_chapter_id` (`chapter_id`) USING BTREE,
  KEY `ix_quiz_records_section_id` (`section_id`) USING BTREE,
  CONSTRAINT `quiz_records_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `quiz_records_ibfk_2` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `quiz_records_ibfk_3` FOREIGN KEY (`subsection_id`) REFERENCES `subsections` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `quiz_records_ibfk_4` FOREIGN KEY (`section_id`) REFERENCES `sections` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=385 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sections` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '小节ID',
  `chapter_id` int NOT NULL COMMENT '所属章节ID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '小节标题',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '小节描述',
  `order` int DEFAULT NULL COMMENT '排序顺序',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_sections_id` (`id`) USING BTREE,
  KEY `ix_sections_chapter_id` (`chapter_id`) USING BTREE,
  CONSTRAINT `sections_ibfk_1` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=164 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subsections` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '小目标ID',
  `section_id` int NOT NULL COMMENT '所属小节ID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '小目标标题（如：1.1.1 掌握核心词汇）',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '目标描述',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '具体的知识点内容（文本）',
  `requirements` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '出题要求与结构化知识点（JSON格式）',
  `weight` float DEFAULT NULL COMMENT '权重占比 (0-100)',
  `passing_score` float DEFAULT NULL COMMENT '合格分数',
  `min_questions` int DEFAULT NULL COMMENT '最少训练题数',
  `order` int DEFAULT NULL COMMENT '排序顺序',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  `user_friendly_requirements` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '用户友好的出题要求描述',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_subsections_section_id` (`section_id`) USING BTREE,
  KEY `ix_subsections_id` (`id`) USING BTREE,
  CONSTRAINT `subsections_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `sections` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=362 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_knowledge_stats` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `knowledge_point_id` int NOT NULL,
  `total_attempts` int DEFAULT NULL COMMENT '总练习次数',
  `correct_attempts` int DEFAULT NULL COMMENT '做对次数',
  `consecutive_errors` int DEFAULT NULL COMMENT '连续做错次数',
  `consecutive_corrects` int DEFAULT NULL COMMENT '连续做对次数',
  `mastery_score` float DEFAULT NULL COMMENT '掌握度评分',
  `last_reviewed_at` datetime DEFAULT NULL COMMENT '上次复习时间',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_user_knowledge_stats_knowledge_point_id` (`knowledge_point_id`) USING BTREE,
  KEY `ix_user_knowledge_stats_user_id` (`user_id`) USING BTREE,
  KEY `ix_user_knowledge_stats_id` (`id`) USING BTREE,
  CONSTRAINT `user_knowledge_stats_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `user_knowledge_stats_ibfk_2` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_points` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=160 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_word_stats` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `subsection_id` int NOT NULL,
  `word` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `count` int DEFAULT NULL COMMENT '练习计数',
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `ix_user_word_stats_user_subsection_word` (`user_id`,`subsection_id`,`word`) USING BTREE,
  KEY `ix_user_word_stats_id` (`id`) USING BTREE,
  KEY `ix_user_word_stats_subsection_id` (`subsection_id`) USING BTREE,
  KEY `ix_user_word_stats_user_id` (`user_id`) USING BTREE,
  KEY `ix_user_word_stats_word` (`word`) USING BTREE,
  CONSTRAINT `user_word_stats_ibfk_1` FOREIGN KEY (`subsection_id`) REFERENCES `subsections` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `user_word_stats_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=194 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名（唯一）',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '电子邮箱',
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '真实姓名',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '密码哈希值',
  `role` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户角色',
  `is_active` int DEFAULT NULL COMMENT '账号状态（1=启用，0=禁用）',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `ix_users_username` (`username`) USING BTREE,
  UNIQUE KEY `ix_users_email` (`email`) USING BTREE,
  KEY `ix_users_role` (`role`) USING BTREE,
  KEY `ix_users_id` (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `wrong_questions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '错题ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `quiz_record_id` int NOT NULL COMMENT '练习记录ID',
  `chapter_id` int NOT NULL COMMENT '章节ID',
  `subsection_id` int DEFAULT NULL COMMENT '小目标ID',
  `question_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '题目类型',
  `question_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '题目内容（JSON格式）',
  `user_answer` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '用户答案',
  `correct_answer` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '正确答案',
  `score` float DEFAULT NULL COMMENT '得分（0-1）',
  `knowledge_point_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '关联知识点ID（JSON数组）',
  `is_mastered` int DEFAULT NULL COMMENT '是否已掌握（1=是，0=否）',
  `retry_count` int DEFAULT NULL COMMENT '重做次数',
  `last_retry_score` float DEFAULT NULL COMMENT '最后一次重做得分',
  `last_retry_at` datetime DEFAULT NULL COMMENT '最后重做时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  `section_id` int DEFAULT NULL COMMENT '节ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `ix_wrong_questions_chapter_id` (`chapter_id`) USING BTREE,
  KEY `ix_wrong_questions_user_id` (`user_id`) USING BTREE,
  KEY `ix_wrong_questions_quiz_record_id` (`quiz_record_id`) USING BTREE,
  KEY `ix_wrong_questions_user_chapter` (`user_id`,`chapter_id`) USING BTREE,
  KEY `ix_wrong_questions_subsection_id` (`subsection_id`) USING BTREE,
  KEY `ix_wrong_questions_id` (`id`) USING BTREE,
  KEY `ix_wrong_questions_question_type` (`question_type`) USING BTREE,
  KEY `ix_wrong_questions_user_mastered` (`user_id`,`is_mastered`) USING BTREE,
  KEY `ix_wrong_questions_section_id` (`section_id`) USING BTREE,
  CONSTRAINT `wrong_questions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `wrong_questions_ibfk_2` FOREIGN KEY (`quiz_record_id`) REFERENCES `quiz_records` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `wrong_questions_ibfk_3` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `wrong_questions_ibfk_4` FOREIGN KEY (`subsection_id`) REFERENCES `subsections` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `wrong_questions_ibfk_5` FOREIGN KEY (`section_id`) REFERENCES `sections` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=661 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

