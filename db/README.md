# 数据库文件

- `schema.sql`：创建 `analytics`、`rag` 表、约束和索引。
- `comments.sql`：为两个 schema 中的每张表和每个字段添加中文注释，由迁移命令自动执行。
- `data.sql`：当前确定性演示库的全量纯数据导出，包含 `analytics` 与 `rag`。
- `legacy_v1_backup.sql`：清理旧版重复表前的结构和数据备份，仅用于历史恢复。
- `legacy_cleanup.sql`：从旧版数据库升级时，在完成备份后清除已被 v3 模型替代的重复对象；全新安装不需要执行。
- `knowledge/*.json`：RAG 业务知识源；运行索引器后写入 `rag.documents`。

恢复到空数据库时，先执行 `schema.sql` 和 `comments.sql`，再执行 `data.sql`。通常更推荐运行项目命令：

```powershell
uv run python -m nl2sql.migrate
psql -U nl2sql -d nl2sql -f db/data.sql
```

`data.sql` 使用 PostgreSQL `COPY` 格式，恢复前应保证目标业务表为空，以免主键冲突。导出中包含知识文档的 1024 维向量数据，因此离线恢复后无需再次调用 Embedding API。
