# HTLB-Platform · GitHub 同类项目与框架设计参考

> 调研日期：2026-10-20  
> 调研对象：GitHub 上与「循证生活指南 / 知识库检索 / 证据链 / 政策时效 / 规则计算 / RAG 评测」相关的项目  
> 数据文件：`01-框架清单.csv`（可排序筛选）、`02-原始数据.json`（28 个仓库详情 + 10 组检索结果）  
> 说明：Star 数为 2026-10-20 快照，只代表关注度，不代表质量或可维护性。

---

## 0. 先看结论

### 0.1 五条判断

1. **直接同类已经出现，但都停在「内容 + 检索」层。**  
   `eternity4719/HowToLiveBetter` 已有 **66,453 Star**，并衍生出微信小程序版、智利本地化版、调研报告和镜像。它们证明内容有需求，但还没有人把「证据时效 + 个人决策记录 + 算账」做成平台。这正是 HTLB-Platform 的差异化空间。

2. **检索层不要从零造轮子，直接借鉴「混合检索 + RRF + 重排 + 引用校验」。**  
   `qmd`（30,495★）和 `knowshelf` 的结构最值得读：BM25 + 向量 + HyDE/查询扩展 → RRF 融合 → LLM/Cross-Encoder 重排 → 返回父块上下文。`life-guide-skill` 则给出了中文场景的 BM25F、近义词、引文逐字校验做法。

3. **「证据链」可以做成产品，而不只是字段。**  
   `arguman` 的论点-支持/反驳树、`hypoarena` 的假设-证据图与贝叶斯累积、`semantica` 的 provenance / decision intelligence，三者组合起来，正好支撑我们的「Decision Trace（决策轨迹）」和 88 条争议条目。

4. **「过期雷达」有现成的工程范式。**  
   `changedetection.io`（35,133★）把「监控 URL → 快照 → 差异 → 条件 → 通知」做成了完整产品。我们只需要把「网页变化」翻译成「条目证据失效」，再加一个人工复核队列。

5. **评测要早做，但不要早造平台。**  
   `promptfoo` + `ragas` / `deepeval` 足够支撑 LifeBench 的第一版：100 条 golden query、Recall@5、引用准确率、拒答正确率，先在脚本和 CI 里跑，稳定后再做后台页面。

### 0.2 建议的技术路线

| 阶段 | 时间 | 重点 | 明确不做 |
|---|---|---|---|
| **P0** | 1–2 周 | 引用校验、来源卡片、决策记录 MVP、20 个高价值来源的雷达、3 个算账器、100 条评测集 | 不引入向量库、不做多智能体、不 fork Dify/RAGFlow |
| **P1** | 3–6 周 | 向量 + BM25 混合检索、RRF、重排、雷达 diff 审核台、只读 MCP、LifeBench CI | 不做通用规则 DSL、不做全量 GraphRAG |
| **P2** | 7–12 周 | 争议条目论证图、证据 lineage、本地化流水线、PWA/小程序、个性化 | 不做医疗诊断、不做投资建议 |

### 0.3 不要做什么

- **不要 fork RAGFlow / Dify / FastGPT 当主系统。** 它们是「通用 AI 应用平台」，会把简单问题复杂化；我们只需要其中的检索、引用、评测模式。
- **不要在 765 条数据规模上引入 Milvus/Neo4j。** MySQL ngram + 可选 Qdrant/OpenSearch 足够；等数据量或查询复杂度真的上来再换。
- **不要一上来做多智能体。** 先把「检索 → 引用 → 回答 → 评测」这条确定性链路跑稳。
- **不要把 Star 当选型依据。** 本清单里既有 15 万 Star 的通用平台，也有 6 Star 但设计极贴合我们场景的项目。
- **不要复制 AGPL/GPL 代码。** 可以学架构，不要抄实现；具体见第 10 节。

---

## 1. 调研方法与数据口径

- 数据来源：GitHub REST API v3（未认证）、重点项目的 README、项目 Topics。
- 覆盖范围：
  - **28 个精选仓库**的完整元数据（Star、Fork、语言、许可证、创建/最近推进、Topics、简介）。
  - **10 组检索**：`howtolivebetter`、`life guide`、`decision journal`、`argument mapping`、`evidence graph`、政策/法规追踪、MCP 知识库、时序知识图谱、RAG 评测、`ruoyi ai`。
  - 其中 `howtolivebetter in:name` 返回 **63 个仓库**，说明已经形成一个小型生态（含镜像、fork、本地化、小程序）。
- 本轮以「元数据 + README 架构」为主，**没有逐仓库 clone 源码**。第 11 节末尾给出了建议做源码级拆解的 5 个仓库。
- Star 数、许可证、最近推进时间均以 2026-10-20 抓取结果为准；GitHub 上的许可证字段可能显示为 `NOASSERTION`，商用前必须打开 LICENSE 原文确认。

### 当前项目基线（对照用）

| 项 | 现状 |
|---|---|
| 后端 | RuoYi 4.8.3（Spring Boot 4.1 + Shiro + Thymeleaf），端口 8088 |
| 前端 | Vue3 + Vite，端口 5176，`/api` 代理到 8088 |
| 数据库 | MySQL `htlb_platform`，`htlb_section` / `htlb_entry`，ngram 全文索引 |
| 知识库 | 34 节 / 765 条；A 495、B 218、C 52；争议 88；上游 commit `5f210ca9` |
| 已有 API | `/api/htlb/stats`、`/entries`、`/entries/{id}`、`/sections`（匿名只读） |
| 缺口 | 来源快照、引用校验、证据时效、决策记录、算账、评测、MCP |

---

## 2. 直接同类：HTLB 生态

### 2.1 清单

| 项目 | Star | 形态 / 栈 | 做了什么 | 可借鉴 | 注意 |
|---|---:|---|---|---|---|
| [eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) | 66,453 | HTML 静态站 | 765 条循证建议，每条有成本、收益、证据等级、原始出处 | 内容结构、证据分级、来源写法；这是我们的上游真源 | CC-BY-4.0，必须署名并注明修改；静态站没有平台能力 |
| [HuiTurn/HowToLiveBetter](https://github.com/HuiTurn/HowToLiveBetter) | 152 | JavaScript / 微信小程序 | 765 条全文搜索、收藏、离线阅读、每日一读 | 移动端信息架构、离线缓存、每日一读的留存设计 | 小程序审核与内容合规；数据同步机制要自建 |
| [ringozzt/howtolivebetter-research](https://github.com/ringozzt/howtolivebetter-research) | 12 | HTML | 上游项目的调研报告 + 思维导图（612 条版本） | “元内容”也能获客：项目分析、思维导图、选型报告 | 版本较旧，引用前核对上游最新数据 |
| [madkoding/HowToLiveBetter-CL](https://github.com/madkoding/HowToLiveBetter-CL) | 8 | Python | 智利本地化：568 条，成本/收益/证据/官方来源；附“把此类指南适配到其他国家”的 Skill | **本地化流水线**：法域、货币、官方来源、文化语境 | 本地化不是翻译，监管与医保规则必须换源 |
| [geekan/HowToLiveLonger](https://github.com/geekan/HowToLiveLonger) | 35,806 | Markdown | 程序员延寿指南，长期维护的循证长寿内容 | 长青内容 + 量化风险表；适合做 SEO 与科普入口 | 领域窄（长寿），没有个人决策层 |
| [yixinagqingyuan/life-guide-skill](https://github.com/yixinagqingyuan/life-guide-skill) | 6 | Python / Codex Skill | 本地知识库 Skill：BM25F、36 组近义表达、三路召回、RRF、规则重排、完整上下文、逐字引文校验 | **最贴近我们检索场景的设计参考**：中文分词、字段加权、引文校验、Agent 分发 | Star 很低；知识库是 676 条旧版，只学方法不搬数据 |

> 相关观察：`howtolivebetter in:name` 共 63 个仓库，包含镜像（30★）、fork（19★）和本地化版本。生态已经出现“重复建设”，缺的是**统一数据 API、来源时效、决策工具**。

### 2.2 五个可借鉴点

1. **内容结构就是数据模型。**  
   上游每条 = 标题 + 说人话 + 收益数字 + 来源 + 四项成本 + 证据等级 + 争议标记。我们的六栏详情页已经对上；下一步要把「来源」从字符串升级为**可校验的 source 实体**。

2. **证据分级要可解释，不要造精确分数。**  
   A/B/C 已经够用。可以增加「来源数量」「是否官方」「最后核验时间」，但不要合成一个看似科学的 0–100 分。

3. **移动端不是缩小版网页。**  
   小程序版的收藏、离线、每日一读值得借鉴；P1 可做 PWA（离线缓存 + 安装），比直接做小程序成本低。

4. **本地化是增长杠杆，也是架构考验。**  
   智利版把“国家/法域/货币/官方来源”抽成可配置层。我们的表结构应预留 `jurisdiction`、`currency`、`effective_date`，不要把中国政策写死在代码里。

5. **“反向内容”也有价值。**  
   检索结果里有一个 `qingchencloud/low-cost-life-guide`（16★，低性价比人生指南：错误建议与高代价决策的反面案例库）。可作为科普/营销模块，但不要和主知识库混在一起。

### 2.3 我们的差异化

| 维度 | 上游 / 衍生 | HTLB-Platform |
|---|---|---|
| 内容 | 静态 Markdown / 小程序 | 结构化 DB + API + 版本 |
| 检索 | 站内搜索 / 本地 BM25 | 混合检索 + 引用校验 + 评测 |
| 时效 | 人工更新 | 来源监控 + 快照 diff + 复核队列 |
| 决策 | 阅读后自己判断 | Decision Trace：记录选择、成本、结果、复盘 |
| 算账 | 文字里的数字 | 规则参数化 + 生效日期 + 计算轨迹 |
| 分发 | 网页 / 小程序 | Web + API + MCP（供 Claude/Codex/Cursor 调用） |

---

## 3. 知识库与 RAG 框架

### 3.1 分层清单

#### A. 轻量检索 / 本地优先（最值得先读源码）

| 项目 | Star | 栈 | 检索设计 | 可借鉴 |
|---|---:|---|---|---|
| [tobi/qmd](https://github.com/tobi/qmd) | 30,495 | TypeScript，本地 GGUF | BM25（SQLite FTS5）+ 向量 + HyDE + 查询扩展；RRF 融合；LLM 重排；**context tree**；MCP | 单机可跑、无外部依赖；`context add` 给文档树补语义；CLI + MCP 双入口 |
| [hi-horan/knowshelf](https://github.com/hi-horan/knowshelf) | 1 | Go + SQLite | Markdown 书籍导入 → 父块（约 2000 字）/ 子块（约 1000 字）；BM25 + 向量 + RRF + 可选重排；MCP Streamable HTTP | **父子块**：子块召回、父块喂给模型；检索日志；SQLite 单文件部署 |
| [yixinagqingyuan/life-guide-skill](https://github.com/yixinagqingyuan/life-guide-skill) | 6 | Python 标准库 | BM25F 字段加权、36 组近义表达、三路召回、RRF、规则重排、完整条目上下文、逐字引文校验 | 中文同义词表；字段权重（标题 > 正文 > 来源）；引文校验；Agent Skill 分发 |

#### B. 平台型知识库 / RAG（看产品能力，不作为底座）

| 项目 | Star | 栈 / 许可证 | 能力 | 可借鉴 | 注意 |
|---|---:|---|---|---|---|
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 92,496 | Go 为主 / Apache-2.0 | 深度文档解析、切块模板、混合检索、Agent | 文档解析与切块策略；引用展示 | 体量大，别整体 fork |
| [langgenius/dify](https://github.com/langgenius/dify) | 158,944 | Python + Next.js / NOASSERTION | 可视化工作流、RAG、Agent、模型接入 | 工作流编排、模型供应商抽象 | 自定义许可证，商用前读原文 |
| [labring/FastGPT](https://github.com/labring/FastGPT) | 29,869 | TypeScript / NOASSERTION | 知识库、RAG、可视化流程 | 知识库与工作流的 UI 组织 | 同上，确认许可证 |
| [1Panel-dev/MaxKB](https://github.com/1Panel-dev/MaxKB) | 23,000 | Python / GPL-3.0 | 企业级智能体、知识库、MCP | 企业后台的信息架构 | GPL：衍生分发需开源 |
| [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) | 67,330 | JavaScript / MIT | 本地优先的 RAG + Agent 工作区 | 本地部署体验、文档接入 | 功能面广，检索深度一般 |
| [open-webui/open-webui](https://github.com/open-webui/open-webui) | 156,206 | Python / NOASSERTION | 自托管 LLM UI、RAG、MCP | 对话式检索的交互 | 品牌/许可证限制，商用确认 |
| [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | 37,752 | Python / AGPL-3.0 | 个人第二大脑、文档/网页问答、自动化 | 个人知识库的产品化路径 | AGPL：网络服务需提供源码 |
| [ageerle/ruoyi-ai](https://github.com/ageerle/ruoyi-ai) | 5,761 | Java / Spring Boot 3.5.8 + LangChain4j / MIT | 多模型管理、知识库 RAG、MCP、Skills、工作流、Supervisor 多智能体 | **若依生态的模块边界**：模型、知识库、工具、工作流、Agent 分层 | 它用 Sa-Token + Spring Boot 3.5，我们是 Shiro + Boot 4.1，不能照搬代码 |

#### C. 图谱 / 记忆 / 高级检索（P2 再看）

| 项目 | Star | 栈 | 特点 | 适用场景 |
|---|---:|---|---|---|
| [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | 40,219 | Python / MIT | 图结构 RAG，实体-关系抽取，增量更新 | 条目之间的因果/引用关系 |
| [microsoft/graphrag](https://github.com/microsoft/graphrag) | 36,388 | Python / MIT | 模块化 GraphRAG，社区摘要，全局/局部查询 | 大规模语料的主题级问答 |
| [getzep/graphiti](https://github.com/getzep/graphiti) | 32,049 | Python / Apache-2.0 | 实时知识图谱，面向 Agent 记忆 | 个人决策随时间变化的关系 |
| [topoteretes/cognee](https://github.com/topoteretes/cognee) | 32,554 | Python / Apache-2.0 | 图 + 向量 + 长期记忆 | 个人上下文/偏好记忆 |
| [Zleap-AI/SAG](https://github.com/Zleap-AI/SAG) | 2,601 | Python / MIT | 宣称新的 RAG 检索架构 + 开放知识库 | 观察检索架构演进 |

> 结论：**P0 不引入图数据库。** 先用 MySQL 把「条目 → 来源 → 快照 → 变更」的外键关系跑通；真正需要多跳推理时，再考虑 LightRAG/Graphiti 或 Neo4j。

### 3.2 五种可复用架构模式

#### 模式 A：混合检索（Hybrid + RRF + Rerank）

```
query
 ├─ 原查询 → BM25 / FTS
 ├─ 查询扩展（同义词 / lex）→ BM25
 ├─ HyDE（LLM 生成假设答案）→ 向量
 └─ 原查询 → 向量
        ↓
   RRF 融合（k=60）
        ↓
   Top 30 → Cross-Encoder / LLM 重排
        ↓
   Top 5–8 → 父块上下文 → 答案 + 引用
```

- `qmd` 的做法：typed sub-queries（`lex` / `vec` / `hyde`）分别路由到 BM25 或向量，再 RRF、再 LLM rerank。
- `knowshelf` 的做法：BM25 与向量各取一批，RRF 后可选 rerank，最后返回 parent chunk。
- 我们的 P0：MySQL ngram BM25 + 同义词扩展；P1 再加向量与 RRF。

#### 模式 B：父子块（Parent–Child Chunking）

- 子块负责**召回**（短、语义集中）；父块负责**生成**（完整段落/条目，避免断章取义）。
- `knowshelf` 的参数可参考：父块约 2000 字、子块约 1000 字；跳过空块与纯标题块。
- 我们的条目本身就是天然父块（一条建议 + 六栏），可以把「说人话/收益/成本/来源」拆成子块，但最终回答必须回到整条。

#### 模式 C：引用可追溯（Citation-first）

- 每条来源保存：URL、标题、发布机构、发布/生效日期、抓取时间、原文快照、引文片段、片段定位（段落/页码）。
- 生成答案时只允许引用**已入库的来源**；引用前做逐字/近似匹配；匹配失败 → 标记「待复核」，不直接展示为已证实。
- `life-guide-skill` 的「逐字引文校验」是最低成本的落地方式。

#### 模式 D：MCP（让 Agent 调用我们的知识库）

- `qmd`、`knowshelf`、`ruoyi-ai` 都提供 MCP。
- 我们可以先做**只读 MCP**：
  - `search_entries(query, grade?, scope?, limit?)`
  - `get_entry(entry_key)`
  - `list_sources(entry_key)`
  - `check_freshness(entry_key)`
- 价值：Claude Code / Codex / Cursor 可以直接查我们的证据库；也倒逼 API 设计稳定。
- 安全：只读、限流、不返回个人信息、不暴露管理接口。

#### 模式 E：工作流 / 多智能体（最后再做）

- Dify/FastGPT/ruoyi-ai 的「可视化工作流 + Supervisor 多智能体」适合复杂任务，但会显著增加调试成本。
- 我们的场景是「检索 → 引用 → 回答/算账」，本质是确定性流水线；P0/P1 用普通 Service 编排即可。

### 3.3 给 HTLB 的检索方案

| 阶段 | 方案 | 具体动作 |
|---|---|---|
| **P0** | MySQL ngram + 规则 | ① 建立同义词表（押金/保证金/定金；裁员/辞退/解雇；医保/医疗保险；工伤/职业伤害…）② 字段加权：标题 > 说人话/收益 > 来源 ③ 保留 grade/scope/ratio/cost 过滤 ④ 记录搜索日志与零结果 ⑤ 1 字查询回退 LIKE |
| **P1** | BM25 + 向量 + RRF | ① embedding 模型（bge-m3 / Qwen3-Embedding / text-embedding-3-small 均可）② 条目向量表或 Qdrant ③ RRF `Σ 1/(60+rank)` ④ Top 30 重排（bge-reranker-v2-m3）⑤ 返回父块（整条 + 来源） |
| **P2** | 图谱 / 多跳 | 条目-来源-政策-结果的关系图；仅当出现「一个决策依赖多条证据」的查询时启用 |

**判断标准**：如果 P0 的 Recall@5 已经 > 0.8，且零结果率 < 5%，不要急着上向量；先把引用准确率和时效做上去。

---

## 4. 证据链、论证与决策轨迹

### 4.1 参考项目

| 项目 | Star | 核心设计 | 对我们有什么用 |
|---|---:|---|---|
| [arguman/arguman.org](https://github.com/arguman/arguman.org) | 1,418 | 论点（claim）→ 前提（premise）→ 支持/反驳边；论证图可视化 | 88 条争议条目的「双方证据」展示；争议详情页的树形结构 |
| [OpSafari/hypoarena](https://github.com/OpSafari/hypoarena) | 555 | 假设-证据图；贝叶斯证据累积；Elo 排序；可复现报告 | 证据权重、争议排序、实验记录；不要直接用于医学结论 |
| [semantica-agi/semantica](https://github.com/semantica-agi/semantica) | 14,140 | 图原生上下文；provenance / lineage；decision intelligence；可解释 AI | 「来源 → 抽取 → 断言 → 决策」的溯源链；Decision Trace 的数据模型 |
| [divijg19/Sage](https://github.com/divijg19/Sage)（检索发现） | 4 | 本地优先、事件溯源的决策日志 | 决策记录的事件化存储；小而可读 |
| [sinameraji/decision-journal-electron](https://github.com/sinameraji/decision-journal-electron)（检索发现） | 6 | 本地、离线、端到端加密的决策日志 | 隐私优先的交互；桌面端可参考 |

> `decision journal` 检索命中 214 个仓库，但高 Star 的几乎没有——这是一个**需求存在、产品未成熟**的信号。

### 4.2 建议的数据模型

```sql
-- 决策主表
htlb_decision (
  id, anon_id, question, context_json,
  chosen_option, expected_cost, expected_benefit,
  confidence, review_at, created_at, updated_at
)

-- 选项（一个决策可以比较多个方案）
htlb_decision_option (
  id, decision_id, label, cost_json, benefit_json, evidence_ids
)

-- 决策引用的证据
htlb_decision_evidence (
  id, decision_id, entry_id, stance, weight, note
)

-- 结果复盘
htlb_decision_review (
  id, decision_id, actual_cost, actual_benefit,
  outcome, satisfaction, reviewed_at
)
```

- `anon_id`：匿名令牌（服务端存哈希），不强制登录也能用；后续可绑定账号。
- `stance`：`support` / `against` / `neutral`；对应争议条目的正反方。
- `confidence`：用户自评 0–100；复盘时可做校准（calibration），但不要误导为概率。
- `review_at`：Quartz 定时提醒；这是留存与数据闭环的关键。

### 4.3 产品形态（Decision Trace MVP）

1. **提问**：用户描述场景（例如「要不要接受这份外地工作？」）。
2. **查证据**：检索相关条目，展示 A/B/C、成本、收益、争议；用户勾选「影响我的证据」。
3. **做选择**：填写选项、预期成本/收益、信心、复盘日期；生成一条决策记录。
4. **到期复盘**：提醒用户填写实际结果；系统对比预期与实际。
5. **导出**：Markdown / JSON；可分享（脱敏）。

价值：
- 对用户：把「看过很多道理」变成「做过有记录的决定」。
- 对平台：积累**匿名决策-结果数据**，未来可做「同类人群的选择分布」「哪条证据最有预测力」。
- 对内容：反向发现「哪些条目被反复引用但结果不好」，驱动内容修订。

合规：
- 明确「不是医疗/法律/投资建议」；高风险场景引导到专业人士。
- 决策记录默认私密；提供一键删除；导出前脱敏。

---

## 5. 时效性：过期雷达

### 5.1 changedetection.io 的流水线

`dgtlmoon/changedetection.io`（35,133★，Apache-2.0）的核心链路：

```
URL / 选择器
   ↓ 定时抓取（可选浏览器步骤，处理 JS 页面）
快照（HTML / 文本 / 视觉）
   ↓ 差异算法
变更（diff）
   ↓ 条件判断（包含/不包含/正则/数值阈值）
通知（Webhook / 邮件 / RSS / Apprise）
   ↓
人工/自动处理
```

可借鉴的工程细节：
- **选择器**：只监控页面中的关键段落，避免整页广告/导航造成噪声。
- **快照留存**：每次抓取存原始内容 + 哈希；diff 可回放。
- **条件**：不是所有变化都值得通知；例如「价格下调 > 5%」「生效日期变化」「文号变化」。
- **通知渠道**：先做 Webhook + 邮件，企业微信/钉钉后置。
- **失败处理**：404/403/超时单独标记，不要当成「内容删除」。
- **合规**：尊重 robots.txt 与 ToS；优先官方 API/RSS；限速；不抓登录后内容。

> 另一个经典模式是 **git-scraping**：定时抓取 → 写入文件 → git commit → 用 `git diff` 看变化。它的优点是天然审计轨迹、可回滚；缺点是仓库会膨胀。我们可以用「数据库快照 + 哈希」实现同样的审计能力。

### 5.2 建议的数据表

```sql
-- 来源登记
htlb_source (
  id, url, title, publisher, doc_type, jurisdiction,
  check_freq, selector, parser, status,
  last_checked_at, last_hash, ttl_days, owner, created_at
)

-- 每次抓取的快照
htlb_source_snapshot (
  id, source_id, fetched_at, http_status,
  content_hash, storage_path, text_excerpt, diff_summary
)

-- 条目与来源的关联（把 sources 字符串升级为实体）
htlb_entry_source (
  id, entry_id, source_id, quote, locator,
  effective_date, expires_at, verified_at, snapshot_id
)

-- 变更事件 + 复核
htlb_change_event (
  id, source_id, old_snapshot_id, new_snapshot_id,
  severity, affected_entry_ids, status,
  reviewed_by, reviewed_at, note
)
```

`status` 建议：`pending`（待复核）→ `confirmed`（已确认）→ `applied`（已更新条目）/ `dismissed`（误报）。

### 5.3 MVP 范围

- **20 个高价值来源**，按领域选：
  - 医保/社保：国家医保局、人社部、各地医保局
  - 住房/租房：住建部、地方住建委
  - 劳动/工伤：人社部、最高法、地方仲裁指南
  - 税务：国家税务总局
  - 安全/健康：WHO、CDC、NHTSA、消费者保护机构
- **频率**：法规/政策每周；统计/指南每月；价格类每日（如做）。
- **流程**：抓取 → 快照 → diff → 规则判定严重度 → 匹配受影响条目（关键词 + 向量相似）→ 人工复核 → 更新条目 + `verified_at`。
- **展示**：条目详情显示「最后核验 / 证据年龄 / 下次检查」；超过 TTL 显示红色「可能过期」。
- **指标**：每周发现变更数、真阳性率、平均修复时间（从变更到条目更新）。

### 5.4 安全注意

- **SSRF**：抓取 URL 必须走域名白名单，禁止内网 IP、`file://`、云元数据地址。
- **HTML 注入**：快照展示前清洗；不要把原始 HTML 直接塞进前端。
- **存储**：快照压缩（gzip）后放 `uploadPath/sources/{sourceId}/{date}.html.gz`，数据库只存路径与摘要。
- **版权**：只存必要片段用于核验；对外展示引文而非整篇转载。

---

## 6. 规则即代码：算账计算器

### 6.1 OpenFisca / PolicyEngine 的启示

| 项目 | Star | 许可证 | 核心 |
|---|---:|---|---|
| [openfisca/openfisca-core](https://github.com/openfisca/openfisca-core) | 247 | AGPL-3.0 | legislation-as-code：把法规写成可执行公式；参数带生效日期；支持微观模拟 |
| [PolicyEngine/policyengine-us](https://github.com/PolicyEngine/policyengine-us) | 169 | AGPL-3.0 | 美国税-benefit 规则引擎 + 微观数据模拟；参数化、可测试 |

它们的共同点：
- **规则与参数分离**：公式是代码，数值（税率、上限、基数）是带生效区间的参数。
- **时间维度是一等公民**：同一规则在不同日期有不同参数。
- **可解释**：计算过程能输出中间变量，而不只是一个结果。
- **可测试**：每个规则有官方示例/边界用例。

> 许可证是 AGPL：**只学设计，不抄代码**。我们如果用 Java 实现自己的小型规则引擎，不存在许可证传染。

### 6.2 我们的设计（P0 先做 3 个）

```sql
htlb_rule (
  id, rule_key, name, jurisdiction,
  effective_from, effective_to, formula,
  source_id, version, created_at
)

htlb_rule_param (
  id, rule_id, param_key, value, unit,
  effective_from, effective_to, source_id
)

htlb_calc_scenario (
  id, rule_key, jurisdiction, inputs_json, created_at
)

htlb_calc_result (
  id, scenario_id, result_json, trace_json, created_at
)
```

P0 建议先做：
1. **经济补偿 N / N+1**（劳动解除场景）
2. **一次性伤残补助金**（工伤，按伤残等级）
3. **租房押金 / 违约金上限**（住房租赁）

每个计算器必须展示：
- 输入项与假设
- 公式（可读文本 + 代码 trace）
- 参数值 + 生效日期 + 来源链接
- 结果区间/边界（不是单一“精确值”）
- 免责声明：不构成法律意见，具体以当地最新规定为准

P1 再做：
- 社保/公积金（城市差异大，参数表要按城市）
- 个税（年度汇算）
- 裁员赔偿与失业金组合
- “假设变更”敏感性分析（例如工资/年限变化）

**不要做通用 DSL。** 先用 Java 类/策略模式实现 3 个规则，参数入库；等规则 > 10 个且非工程同学也要维护时，再考虑 YAML/JSON DSL。

---

## 7. 评测：LifeBench

### 7.1 参考框架

| 项目 | Star | 许可证 | 适合做什么 |
|---|---:|---|---|
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 26,158 | MIT | 声明式 YAML 测试、CI/CD、RAG 红队、模型对比 |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | 18,968 | Apache-2.0（以仓库为准） | pytest 风格的 LLM 评测；指标可组合 |
| [vibrantlabsai/ragas](https://github.com/vibrantlabsai/ragas) | 16,076 | Apache-2.0 | RAG 指标：faithfulness、answer relevancy、context precision/recall |
| [modelscope/evalscope](https://github.com/modelscope/evalscope) | 3,563 | Apache-2.0（以仓库为准） | 模型能力/性能评测，适合选型对比 |

### 7.2 指标与数据集

**第一版 100 条 golden query**，覆盖：
- 每个 section 至少 2 条
- 高频生活场景（租房、医保、工伤、裁员、育儿、急救）
- 边界/歧义/过时/争议问题
- 应拒答的问题（无证据、医疗诊断、投资建议）

指标：

| 类别 | 指标 | 说明 |
|---|---|---|
| 检索 | Recall@5 / MRR@10 / nDCG@10 | 期望条目是否在前 5；排序质量 |
| 引用 | URL 有效率 / 引文匹配率 / 来源权威性 | 链接可访问；引文能在快照中逐字/近似匹配 |
| 回答 | Groundedness / 拒答正确率 | 回答是否只基于检索证据；无证据时是否拒答 |
| 时效 | TTL 通过率 / 平均证据年龄 | 过期来源比例 |
| 性能 | P95 延迟 / 零结果率 | 体验基线 |

### 7.3 落地方式

- **P0**：Python 脚本读取 `eval_cases.json` → 调 `/api/htlb/entries` → 计算 Recall@5、引用有效率 → 输出 JSON/Markdown 报告。
- **P1**：promptfoo YAML 做回归；GitHub Actions 或本地定时任务；结果写 `htlb_eval_run`。
- **P2**：后台仪表盘；每次内容导入自动跑；Recall 下降 > 5% 阻止发布。

**关键原则**：评测集必须独立于开发时的调参样本；不要用“我们挑过的 10 条”证明系统好用。

---

## 8. 目标架构（HTLB-Platform）

### 8.1 模块图

```
┌─────────────────────────────────────────────────────┐
│  htlb-ui  Vue3 + Vite  :5176                        │
│  检索 / 条目 / 决策记录 / 雷达 / 算账 / 评测          │
└──────────────────────┬──────────────────────────────┘
                       │ /api（Vite proxy）
┌──────────────────────▼──────────────────────────────┐
│  htlb-admin  RuoYi 4.8.3  :8088  (Shiro + Thymeleaf) │
│  ├─ htlb-knowledge   条目 / 章节 / 检索 / 引用（已有）│
│  ├─ htlb-evidence    来源 / 快照 / 变更 / 决策（新增）│
│  ├─ htlb-calc        规则 / 参数 / 算账（新增）       │
│  └─ htlb-bench       评测任务与报告（可先放 tools/）  │
└──────────────┬───────────────────────┬───────────────┘
               │                       │
        MySQL htlb_platform      本地 uploadPath / MinIO
        （+ Quartz 定时）          （来源快照、导出文件）
               │
     可选：OpenSearch / Qdrant + Embedding/Rerank 模型
```

### 8.2 新增模块与职责

| 模块 | 职责 | 优先级 | 说明 |
|---|---|---|---|
| `htlb-knowledge` | 条目、章节、检索、引用字段 | 已有 | 继续做只读 API；补 source 关联 |
| `htlb-evidence` | source / snapshot / change / decision | P0 | 把“来源字符串”升级为实体；决策记录也放这里 |
| `htlb-calc` | rule / param / scenario / result | P0 | 先 3 个规则，参数入库 |
| `htlb-bench` | eval case / run / report | P1 | 早期用 Python 脚本，不急着建模块 |
| `htlb-radar` | 抓取、diff、复核 | P1 | 也可以并入 `htlb-evidence`，避免模块过多 |

> 建议 P0 只新增 **2 个 Maven 模块**：`htlb-evidence`、`htlb-calc`。雷达先作为 `htlb-evidence` 的子包；评测先放 `tools/eval/`。模块太多会让若依的构建和权限配置变复杂。

### 8.3 新增表（DDL 级别）

| 表 | 作用 |
|---|---|
| `htlb_source` | 来源登记：URL、机构、类型、法域、频率、TTL |
| `htlb_source_snapshot` | 每次抓取的快照、哈希、存储路径 |
| `htlb_entry_source` | 条目-来源-引文-定位-生效/过期时间 |
| `htlb_change_event` | 变更事件、严重度、受影响条目、复核状态 |
| `htlb_decision` | 决策主表 |
| `htlb_decision_option` | 决策选项 |
| `htlb_decision_evidence` | 决策引用的证据 |
| `htlb_decision_review` | 结果复盘 |
| `htlb_rule` / `htlb_rule_param` | 规则与参数（带生效区间） |
| `htlb_calc_scenario` / `htlb_calc_result` | 算账输入、结果与计算轨迹 |
| `htlb_eval_case` / `htlb_eval_run` | 评测集与运行结果 |
| `htlb_search_log` | 查询、过滤、结果、点击、耗时 |

### 8.4 API 草图

```http
# 已有
GET  /api/htlb/stats
GET  /api/htlb/sections
GET  /api/htlb/entries?q=&grade=&scope=&pageNum=&pageSize=
GET  /api/htlb/entries/{entryKey}

# 证据与来源
GET  /api/htlb/entries/{entryKey}/sources
GET  /api/htlb/sources?status=&jurisdiction=
GET  /api/htlb/sources/{id}/snapshots
GET  /api/htlb/changes?status=pending
POST /api/htlb/changes/{id}/review      # admin

# 决策记录（匿名令牌）
POST /api/htlb/decisions
GET  /api/htlb/decisions/{id}
POST /api/htlb/decisions/{id}/review
DELETE /api/htlb/decisions/{id}

# 算账
POST /api/htlb/calc/{ruleKey}
GET  /api/htlb/calc/rules
GET  /api/htlb/calc/rules/{ruleKey}/params?at=2026-10-20

# 评测（admin）
GET  /api/htlb/eval/runs
GET  /api/htlb/eval/runs/{id}
```

约定：
- 匿名只读接口继续用类级 `@Anonymous`；写接口用匿名令牌 + 限流，管理接口走 Shiro。
- 统一返回 `AjaxResult`（code=0 成功）；分页用 `TableDataInfo`。
- `entryKey` 保持 `s01e01` 形式，便于外链和 MCP。

### 8.5 前端页面

| 页面 | 内容 | 优先级 |
|---|---|---|
| 检索页（已有） | 搜索、筛选、结果卡、零结果引导 | P0 增强 |
| 条目详情（已有） | 六栏 + 来源卡片 + 证据年龄 + 争议双方 | P0 增强 |
| 决策记录 | 3 步向导、列表、复盘提醒、导出 | P0 |
| 过期雷达 | 来源列表、diff 查看、影响条目、复核按钮 | P1 |
| 算账 | 表单、结果、公式 trace、来源与免责声明 | P0/P1 |
| 评测后台 | 运行记录、指标趋势、失败样例 | P2 |

交互细节：
- 详情页来源卡片显示：机构、标题、发布日期、最后核验、`有效 / 可能过期 / 待复核` 徽章、快照 diff 入口。
- 争议条目：左右两栏「支持证据 / 反对证据」，中间显示结论；不要只放一个“争议”标签。
- 搜索无结果：给出同义词建议、相邻条目、提交缺失需求的入口。

---

## 9. 路线图与验收

### P0（1–2 周）

| 任务 | 验收 |
|---|---|
| 来源实体化：`htlb_source` + `htlb_entry_source`，导入现有 sources | 至少 80% 条目有结构化来源；可点开链接 |
| 引用校验脚本 | 对 50 条抽样，URL 有效率 ≥ 90%，引文匹配率 ≥ 70% |
| 详情页来源卡片 + 证据年龄 | 过期/待复核状态可见 |
| 决策记录 MVP | 创建、查看、到期复盘、导出；匿名可用 |
| 3 个算账器 | 每个有参数、公式、来源、单元测试、免责声明 |
| 20 个来源的雷达 | 每周抓取；diff 可查看；待复核队列可用 |
| 100 条 golden query | 报告 Recall@5、引用有效率、零结果率 |

### P1（3–6 周）

- 向量检索 + RRF + 重排；Recall@5 相对 P0 提升 ≥ 10%。
- 雷达 diff 审核台：确认/驳回/批量更新；平均处理时间 < 10 分钟/条。
- 只读 MCP：`search_entries` / `get_entry` / `list_sources` / `check_freshness`。
- LifeBench CI：每次内容导入自动跑；指标回落可见。
- 搜索日志分析：零结果 Top 20、点击率、慢查询。

### P2（7–12 周）

- 争议条目论证图（arguman 风格）。
- 证据 lineage（semantica 风格）：来源 → 快照 → 引文 → 条目 → 决策。
- 本地化流水线（madkoding 风格）：法域/货币/官方来源配置。
- PWA/小程序；离线阅读、每日一读。
- 个性化：基于决策记录与收藏的推荐（注意隐私与回音室）。

### 成功指标

| 维度 | 指标 |
|---|---|
| 内容 | 有结构化来源的条目占比；平均证据年龄；过期条目占比 |
| 检索 | Recall@5；零结果率；P95 延迟；点击率 |
| 决策 | 决策记录创建数；复盘完成率；用户满意度 |
| 雷达 | 每周变更数；真阳性率；从变更到条目更新的时间 |
| 分发 | API/MCP 调用量；外链打开率 |

---

## 10. 许可证与风险

### 10.1 许可证速查

| 许可证 | 代表项目 | 能不能用 | 注意 |
|---|---|---|---|
| CC-BY-4.0 | HowToLiveBetter、小程序版 | 可以，需署名 | 必须注明来源、许可证、是否修改；不要求衍生同样开源 |
| MIT | qmd、ruoyi-ai、LightRAG、GraphRAG、AnythingLLM、SAG、semantica、hypoarena、promptfoo | 最宽松 | 保留版权与许可声明 |
| Apache-2.0 | RAGFlow、knowshelf、Graphiti、Cognee、changedetection | 宽松 + 专利授权 | 保留 NOTICE；注意商标 |
| GPL-3.0 | MaxKB | 强 copyleft | 分发衍生作品需开源；内部使用通常没问题 |
| AGPL-3.0 | Khoj、OpenFisca、PolicyEngine | 网络服务也触发 | 修改后提供网络服务需提供源码；**只学设计** |
| NOASSERTION | Dify、FastGPT、Open WebUI、Arguman | 未知/自定义 | 商用前必须读 LICENSE 原文 |

> 本表依据 GitHub API 的 `license.spdx_id`；它可能识别失败。任何商用/分发前，请让法务确认。

### 10.2 内容与合规风险

1. **上游内容许可**：我们已导入 HowToLiveBetter（CC-BY-4.0）。页脚与条目详情应显示：
   - 来源：HowToLiveBetter
   - 许可证：CC-BY-4.0
   - 上游 commit：`5f210ca9…`
   - 是否修改：是（结构化、检索、补充来源）
2. **医疗/法律/金融建议**：全站免责声明；高风险问题引导专业人士；不要根据用户情况给出个性化诊断/投资建议。
3. **抓取合规**：优先官方 API/RSS；遵守 robots.txt 与 ToS；限速；不抓登录后内容；提供删除/更正渠道。
4. **隐私**：决策记录默认私密；匿名令牌可删除；导出脱敏；不要训练第三方模型。
5. **LLM 幻觉**：只允许引用已入库来源；无证据拒答；引用校验失败降级为“未核验”。
6. **SSRF/HTML 注入**：来源抓取白名单；快照清洗；禁止内网地址。
7. **上游漂移**：每周检查上游 commit；导入脚本保留 `sync_meta.json`；变更 diff 人工复核。
8. **Star 通胀**：本清单中不少项目 Star 很高但领域不同（如 public-apis）；选型看提交活跃度、issue 质量、许可证、是否解决我们的问题。

---

## 11. 参考链接总表

### 直接同类

- https://github.com/eternity4719/HowToLiveBetter
- https://github.com/HuiTurn/HowToLiveBetter
- https://github.com/ringozzt/howtolivebetter-research
- https://github.com/madkoding/HowToLiveBetter-CL
- https://github.com/geekan/HowToLiveLonger
- https://github.com/yixinagqingyuan/life-guide-skill

### 知识库 / RAG

- https://github.com/tobi/qmd
- https://github.com/hi-horan/knowshelf
- https://github.com/ageerle/ruoyi-ai
- https://github.com/infiniflow/ragflow
- https://github.com/langgenius/dify
- https://github.com/labring/FastGPT
- https://github.com/1Panel-dev/MaxKB
- https://github.com/Mintplex-Labs/anything-llm
- https://github.com/open-webui/open-webui
- https://github.com/khoj-ai/khoj
- https://github.com/Zleap-AI/SAG
- https://github.com/HKUDS/LightRAG
- https://github.com/microsoft/graphrag
- https://github.com/getzep/graphiti
- https://github.com/topoteretes/cognee

### 证据链 / 论证 / 决策

- https://github.com/arguman/arguman.org
- https://github.com/OpSafari/hypoarena
- https://github.com/semantica-agi/semantica
- https://github.com/divijg19/Sage
- https://github.com/sinameraji/decision-journal-electron

### 时效监控

- https://github.com/dgtlmoon/changedetection.io

### 规则即代码

- https://github.com/openfisca/openfisca-core
- https://github.com/PolicyEngine/policyengine-us

### 评测

- https://github.com/promptfoo/promptfoo
- https://github.com/confident-ai/deepeval
- https://github.com/vibrantlabsai/ragas
- https://github.com/modelscope/evalscope

### 若依生态（选型背景）

- https://github.com/yangzongzhuan/RuoYi
- https://github.com/yangzongzhuan/RuoYi-Vue
- https://github.com/YunaiV/ruoyi-vue-pro
- https://github.com/ageerle/ruoyi-ai
- https://github.com/ageerle/ruoyi-web

### 建议做源码级拆解的 5 个仓库

1. **tobi/qmd**（TypeScript）：看 typed sub-query、HyDE、RRF、LLM rerank、context tree、MCP 的工程实现。
2. **hi-horan/knowshelf**（Go）：看 Markdown 导入、父子块切分、SQLite FTS5 + sqlite-vec、RRF、MCP HTTP。
3. **ageerle/ruoyi-ai**（Java）：看若依生态如何划分模型/知识库/工具/工作流/Agent 模块；只学边界，不抄代码。
4. **dgtlmoon/changedetection.io**（Python）：看抓取调度、选择器、diff、条件、通知、失败重试。
5. **arguman/arguman.org**（Django）：看论点-前提-支持/反驳的数据模型与可视化；项目已停更，只学模型。

---

## 附录 A：检索查询与命中量

| 查询 | GitHub total_count | 说明 |
|---|---:|---|
| `howtolivebetter in:name` | 63 | 已形成生态：镜像、fork、本地化、小程序 |
| `"life guide" in:name,description` | 334 | 大量校园/留学/生活方式指南，相关性参差 |
| `"decision journal" in:name,description` | 214 | 需求存在，但高 Star 产品少 |
| `"argument mapping" in:name,description` | 62 | 小众；arguman 是最完整的开源实现 |
| `"evidence graph" in:name,description` | 338 | 多为科研/安全/开发工具，生活决策场景空白 |
| `policy OR regulation tracker in:name,description stars:>50` | 7,000 | 噪声大；没有找到比 changedetection 更通用的开源方案 |
| `mcp knowledge base in:name,description stars:>100` | 22 | MCP 知识库正在升温（5ire、EdgeEver、Arkon 等） |
| `temporal knowledge graph in:name,description stars:>300` | 5 | 偏学术/通用图技术，生活场景需二次设计 |
| `deepeval OR ragas OR evalscope in:name` | 2,246 | 评测框架生态成熟，直接选型即可 |
| `ruoyi ai in:name,description` | 197 | 若依 AI 生态活跃；ruoyi-ai 最贴近 |

> `total_count` 是 GitHub 搜索的估算值，会随时间变化；仅用于判断生态规模，不代表质量。

## 附录 B：文件说明

| 文件 | 内容 | 用法 |
|---|---|---|
| `README.md` | 本文件：结论、架构模式、落地方案 | 先读这个 |
| `01-框架清单.csv` | 28 个仓库的分类、Star、语言、许可证、链接、简介 | Excel 排序/筛选；做选型表 |
| `02-原始数据.json` | 28 个仓库完整元数据 + 10 组检索的 Top 8 结果 | 程序化处理；二次分析 |

### 数据字段说明（JSON）

- `meta`：抓取时间、来源、口径说明。
- `repos[]`：`category`（direct/kb/evidence/monitor/rules/eval）、`repo`、`stars`、`forks`、`language`、`license`、`created`、`pushed`、`topics`、`description`、`url`。
- `queries[]`：`q`、`total`、`items[]`（repo/stars/language/pushed/description/url）。

---

**下一步建议**：先做 P0 的三件事——来源实体化 + 引用校验、决策记录 MVP、20 个来源的过期雷达。它们都不依赖向量库或大模型，能在现有若依 + Vue3 架构上直接落地，并且最能形成与静态指南类项目的差异。
