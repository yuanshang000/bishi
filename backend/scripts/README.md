# 维护脚本目录

本目录包含系统维护和数据处理相关的脚本工具。

## 📁 目录结构

```
scripts/
├── README.md           # 本说明文档
└── reset_vectors.py    # 向量数据重置与重建脚本
```

## 📜 脚本说明

### 1. reset_vectors.py - 向量数据重置脚本

**用途：** 重置并重建 ChromaDB 向量数据库中的所有向量数据

**使用场景：**
- 向量数据损坏，需要重建
- 更换 Embedding 模型后，需要重新生成向量
- 数据迁移后，需要重建向量索引
- 测试环境数据重置

**执行方法：**
```bash
# 在 backend 目录下执行
cd backend
python scripts/reset_vectors.py
```

**执行流程：**
1. 清空 ChromaDB 中的所有向量数据
2. 重置数据库中的向量化标志（is_vectorized = 0）
3. 重新向量化所有课程文档（CourseDocument）
4. 重新向量化所有小节内容（SubSection）

**注意事项：**
- ⚠️ 此操作会清空所有向量数据，请谨慎使用
- ⚠️ 执行时间取决于文档数量，可能需要较长时间
- ⚠️ 建议在非高峰期执行
- ⚠️ 执行前请确保数据库连接正常，Embedding API 可用

**依赖：**
- ChromaDB（向量数据库）
- Embedding API（向量生成服务）
- MySQL 数据库

## 🔧 使用建议

### 执行前检查

1. **确认数据库连接正常**
   ```bash
   # 测试数据库连接
   mysql -u root -p college_english_assistant
   ```

2. **确认 Embedding API 可用**
   - 检查 `.env` 文件中的 `EMBEDDING_API_KEY`
   - 测试 API 连接是否正常

3. **备份数据（可选）**
   ```bash
   # 备份 ChromaDB 数据
   cp -r data/chroma data/chroma_backup
   ```

### 执行时机

- ✅ 开发/测试环境：随时可以执行
- ✅ 生产环境：建议在维护窗口或低峰期执行
- ❌ 用户活跃期：避免执行，影响性能

### 执行后验证

1. **检查向量数量**
   - 查看脚本输出的成功/失败统计
   - 确认所有文档都已成功向量化

2. **测试 RAG 检索**
   - 使用聊天功能测试检索效果
   - 确认能正确检索到相关内容

3. **检查数据库状态**
   ```sql
   -- 查看向量化状态
   SELECT COUNT(*) FROM course_documents WHERE is_vectorized = 1;
   SELECT COUNT(*) FROM subsections WHERE is_vectorized = 1;
   ```

## 📝 添加新脚本

如果需要添加新的维护脚本，请遵循以下规范：

1. **文件命名**
   - 使用小写字母和下划线
   - 名称清晰表达功能
   - 例如：`import_data.py`、`clean_cache.py`

2. **添加文档注释**
   - 在文件开头添加详细的文档字符串
   - 说明用途、使用方法、注意事项
   - 参照 `reset_vectors.py` 的格式

3. **更新本 README**
   - 在"脚本说明"部分添加新脚本的描述
   - 更新目录结构图

## 🆘 常见问题

### Q1: reset_vectors.py 执行失败怎么办？

**A:** 检查以下几点：
1. 数据库连接是否正常
2. Embedding API 是否可用
3. ChromaDB 目录权限是否正确
4. 查看错误日志，定位具体问题

### Q2: 向量化速度很慢怎么办？

**A:** 可能的原因：
1. 文档数量过多 - 正常现象，耐心等待
2. Embedding API 响应慢 - 检查网络连接
3. 数据库性能问题 - 优化数据库配置

### Q3: 可以只向量化部分文档吗？

**A:** 当前脚本会向量化所有文档。如需部分向量化，可以：
1. 修改脚本，添加筛选条件
2. 或手动调用 `rag_service.vectorize_document()` 方法

## 📞 技术支持

如有问题，请联系系统管理员或查看项目文档。
