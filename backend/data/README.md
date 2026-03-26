# 数据存储目录

本目录用于存储系统运行时产生的各类数据文件。

## 📁 目录结构

```
data/
├── chroma/                    # ChromaDB 向量数据库（系统必需）
│   ├── chroma.sqlite3        # SQLite 数据库文件
│   └── [collection_id]/      # 向量集合目录
├── test_structure.txt         # 测试结构示例文件
└── README.md                  # 本说明文档
```

## 🗄️ chroma 目录

### ⚠️ 重要说明

**此目录为系统必需目录，请勿删除！**

### 用途

ChromaDB 向量数据库的持久化存储目录，用于：

1. **文档向量化存储**
   - 存储课程文档的向量嵌入
   - 支持语义搜索和相似度检索

2. **RAG（检索增强生成）**
   - 为 AI 问答提供上下文检索
   - 提高回答的准确性和相关性

3. **知识点检索**
   - 快速查找相关知识点
   - 支持智能推荐和关联分析

### 配置

在 `app/core/config.py` 中配置：

```python
CHROMA_PERSIST_DIR: str = "./data/chroma"
CHROMA_COLLECTION_NAME: str = "course_embeddings"
```

### 使用位置

```python
# app/services/rag_service.py
self.chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)
```

### 数据内容

- **chroma.sqlite3**：ChromaDB 的元数据数据库
- **[collection_id]/**：向量集合数据目录
  - 存储实际的向量数据
  - 支持高效的向量检索

### 工作流程

```
文档上传
    ↓
文本解析与分块
    ↓
Embedding API 生成向量
    ↓
存储到 ChromaDB (data/chroma/)
    ↓
更新数据库记录 (chroma_ids)
```

### 检索流程

```
用户提问
    ↓
问题向量化
    ↓
ChromaDB 相似度检索
    ↓
返回相关文档片段
    ↓
提供给 LLM 生成回答
```

### 维护建议

1. **定期备份**
   ```bash
   # 备份 ChromaDB 数据
   tar -czf chroma_backup.tar.gz data/chroma/
   ```

2. **监控大小**
   ```bash
   # 查看目录大小
   du -sh data/chroma/
   ```

3. **数据重建**
   - 使用 `scripts/reset_vectors.py` 重建向量数据
   - 适用于更换 Embedding 模型或数据损坏

### ⚠️ 注意事项

- ❌ 不要删除此目录
- ❌ 不要手动修改数据库文件
- ✅ 定期备份重要数据
- ✅ 监控磁盘空间使用

---

## 📄 test_structure.txt 文件

### 用途

测试用的章节结构示例文件，包含：

- 章节结构示例
- 小目标定义
- 知识点示例
- 例句和说明

### 内容示例

```
[章节] 英语基础（测试）
[节] 颜色与形容词
[小目标] 掌握颜色词汇与简单描述
●权重占比：10%
●合格分数：60分

核心内容：
- red 表示红色，用于描述物体颜色
- blue 表示蓝色，用于描述天空或海洋
...
```

### 使用场景

- 作为章节结构的参考示例
- 测试章节解析功能
- 演示知识点组织方式

### 是否必需

- ⚠️ 非系统必需
- ✅ 建议保留作为示例参考
- 可以删除，不影响系统功能

---

## 🔧 相关功能

### 向量化服务

**文件：** `app/services/rag_service.py`

**功能：**
- 文档向量化
- 语义检索
- 相似度计算

### 重置脚本

**文件：** `scripts/reset_vectors.py`

**功能：**
- 清空向量数据
- 重建向量索引
- 修复向量问题

**使用方法：**
```bash
cd backend
python scripts/reset_vectors.py
```

---

## 📊 数据统计

### 查看向量数量

```python
# 在 Python 中查询
from app.services.rag_service import rag_service

count = rag_service.collection.count()
print(f"向量数量: {count}")
```

### 查看数据库记录

```sql
-- 查询已向量化的文档
SELECT id, title, is_vectorized, vector_count
FROM course_documents
WHERE is_vectorized = 1;
```

---

## 🔄 数据迁移

### 迁移向量数据

如果需要迁移 ChromaDB 数据：

1. **备份现有数据**
   ```bash
   cp -r data/chroma data/chroma_backup
   ```

2. **复制到新环境**
   ```bash
   # 在新环境中
   cp -r chroma_backup data/chroma
   ```

3. **验证数据完整性**
   - 检查向量数量
   - 测试检索功能
   - 验证 RAG 效果

---

## 🗑️ 清理建议

### 可以删除的内容

- ✅ 旧版本数据目录（如 `chroma_v2`）
- ✅ 测试数据（如果不需要）

### 不能删除的内容

- ❌ `chroma/` 目录（系统必需）
- ❌ `chroma.sqlite3` 文件（向量数据库）

---

## 📞 故障排查

### 问题：向量检索失败

**可能原因：**
1. ChromaDB 数据损坏 → 使用 `reset_vectors.py` 重建
2. 目录权限问题 → 检查目录权限
3. 磁盘空间不足 → 清理空间

### 问题：向量化速度慢

**可能原因：**
1. 文档数量过多 → 正常现象
2. Embedding API 响应慢 → 检查网络
3. 磁盘 I/O 慢 → 优化存储

### 问题：数据丢失

**解决方案：**
1. 从备份恢复
2. 使用 `reset_vectors.py` 重建
3. 重新上传文档

---

## 📚 相关文档

- [RAG 服务](../app/services/rag_service.py)
- [系统配置](../app/core/config.py)
- [向量重置脚本](../scripts/reset_vectors.py)
- [文档模型](../app/models/document.py)

---

**最后更新：** 2026-03-26
**维护人员：** 系统管理员
