# NL2SQL RAG 教学项目

一个可运行的中文全渠道电商数据分析助手。Google ADK 管理 Agent，DeepSeek 生成 PostgreSQL 查询，Qwen Embedding + pgvector 检索表结构与业务口径。数据域覆盖订单、商品、支付、退款、会员、营销、流量和履约。[`tutorial/` 教程](tutorial/README.md) 用分章节 Notebook 讲解通用 RAG 方案和本项目的工程实现。

## 快速开始（PowerShell）

要求：Docker Desktop、`uv`、Python 3.12（`uv` 可自动管理）。

```powershell
Copy-Item .env.example .env
# 编辑 .env 中的 QWEN_API_KEY、DEEPSEEK_API_KEY；如百炼使用专用业务空间，还需填写 DASHSCOPE_BASE_URL
# 若密钥已登记为 Windows 用户级环境变量，但当前终端尚未继承它：
if (-not $env:QWEN_API_KEY) { $env:QWEN_API_KEY = [Environment]::GetEnvironmentVariable('QWEN_API_KEY', 'User') }
docker compose up -d db
uv sync --extra dev
uv run python -m nl2sql.migrate
uv run python -m nl2sql.seed
uv run python -m nl2sql.indexer
uv run adk web .
```

在 ADK Web 中选择 `nl2sql_agent`。例如问：“2026 年 8 月华东地区已支付订单的净销售额是多少？” ADK Web 是开发调试界面。接口服务可用 `uv run adk api_server .` 启动。

若数据库中仍是早期 800 单演示数据，普通种子命令会停止并提示确认。明确要替换旧的生成式演示数据时使用 `uv run python -m nl2sql.seed --reset`；该参数会重建 `analytics` 中的演示事实。

> 不要将真实密钥写入 Notebook 或提交到仓库。`.env` 已被 Git 忽略。当前样例密码仅供本地开发，应在其他环境更换。

## 评估与测试

```powershell
uv run pytest -q
uv run pytest -q -m integration
uv run adk eval nl2sql_agent tests/eval/core.evalset.json --config_file_path tests/eval/eval_config.json --print_detailed_results
uv run adk eval nl2sql_agent tests/eval/safety.evalset.json --config_file_path tests/eval/safety_config.json
uv run python -m nl2sql.evaluate_retrieval --strategies lexical vector hybrid
```

`adk eval` 会真实调用 DeepSeek；分析用例还会调用 Qwen，并要求已完成数据库初始化和索引。由于自然语言输出存在变化，ADK Eval 关注工具调用路径；精确的 SQL 安全性和数据结果由 `pytest` 检查。分析 Eval 覆盖会员、单表统计、跨表关联、指标口径、营销、履约和多轮追问；安全 Eval 检查写入请求不触发任何工具。

`evaluate_retrieval` 使用 150 条人工标注问题计算 Recall@5/10、MRR、nDCG、最终上下文召回率和必需表覆盖率，可直接比较纯词法、纯向量和混合检索。`vector` 与 `hybrid` 会真实调用 Qwen 查询嵌入。

## 数据与 RAG

`analytics` schema 对 Agent 开放 22 张业务表，包括客户、四级会员及等级历史、商品两级分类、销售渠道、营销活动、订单与优惠、支付重试与分次支付、退款商品、拆单包裹、访问会话、活动日费用、仓库、供应商、商品供货关系、库存快照、商品评价和财务日历。固定随机种子生成 10,000 个客户、500 个商品、30,000 个订单、约 75,000 条订单明细、100,000 个会话、24,000 条库存快照和 7,699 条商品评价，时间覆盖 2024 年 10 月至 2026 年 9 月。

会员等级为普通、黄金、白金和钻石，对应会员减免率 0%、5%、10% 和 15%，并保存等级有效期历史与下单时快照。种子数据还包含季节性活动、会员升级、活动后叠加会员折扣、支付失败重试、分次支付、部分退款、跨月退款、拆单配送和延迟送达等可重复业务场景。

`db/knowledge/` 包含 142 张分域知识卡：表说明、指标口径、关联规则、枚举、歧义词和已审核 SQL 思路。索引器追加实时字段清单，对内容及依赖元数据计算哈希，只重新向量化变化文档。入库调用 Qwen `text_type=document`，查询调用 `text_type=query`，固定 1024 维；运行时结合 pgvector 余弦相似度、显式别名匹配、加权 RRF 和知识依赖扩展。可用 `ENABLE_RAG_RERANK=true` 打开候选重排实验。模型或维度变化需要重建索引和相应数据库列。

本项目使用 DashScope 原生 Embedding API，以支持 `query`/`document` 区分。百炼业务空间专用 Host 的配置格式为 `https://<workspace-id>.<region>.maas.aliyuncs.com/api/v1`。OpenAI 兼容地址末尾的 `/compatible-mode/v1` 不能直接作为 `DASHSCOPE_BASE_URL`；应改为 `/api/v1`。

生成的 SQL 经 SQLGlot 解析，仅允许一条 `SELECT`，并检查表白名单。执行连接使用只能读取 `analytics` 的数据库角色、只读事务、5 秒超时和最多 100 行的外层限制。此项目展示防护层次，但在真实组织中仍应根据数据敏感级别加入身份验证、租户隔离和审计策略。

## 目录

- `nl2sql_agent/`：ADK 入口和函数工具。
- `src/nl2sql/`：应用配置、数据库、Embedding、索引、检索和安全执行。
- `db/`：DDL、全表字段注释、SQL 数据导出与按领域拆分的知识目录。
- `tests/`：单元、集成和 ADK Eval 用例。
- `tutorial/`：分章节 Notebook、阅读路线和每章工程练习。

## 常见问题

- **Qwen 401/404**：检查 `QWEN_API_KEY`，以及业务空间的 `DASHSCOPE_BASE_URL` 是否指向 `/api/v1`。环境变量需对运行 `uv` 的进程可见。
- **数据库连接失败**：先检查 `docker compose ps`；若更改 Compose 密码但保留旧数据卷，数据库原有密码不会自动改变。
- **知识索引为空**：先运行 `python -m nl2sql.indexer`；需要可用的 Qwen 密钥。
- **Windows 编码错误**：可在当前 PowerShell 会话设置 `$env:PYTHONUTF8 = '1'`。
