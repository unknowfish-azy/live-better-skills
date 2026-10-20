# life-scene-cv-advisor · 视觉循证生活顾问

> 一个 WorkBuddy / Agent Skills 技能包：用户**上传一张照片**（厨房、药箱、工位、出租屋、合同借条、转账截图、街景、家人照片），用多模态视觉读懂场景，再映射到《高性价比人生指南》**765 条循证条目**，按「性价比档 + 证据等级」排序，输出**每条都能指回图中要素和书中条号**的行动清单。

![version](https://img.shields.io/badge/version-1.0.0-blue)
![skill](https://img.shields.io/badge/type-agent%20skill-orange)
![data](https://img.shields.io/badge/data-765%20entries%20%2F%2034%20sections-green)
![upstream](https://img.shields.io/badge/upstream-HowToLiveBetter-lightgrey)
![license](https://img.shields.io/badge/code-MIT-yellow)
![data license](https://img.shields.io/badge/content-CC%20BY%204.0-yellow)

---

## 一、命名与唯一性

### 为什么叫这个名字

| 项 | 值 | 说明 |
|---|---|---|
| **仓库名** | `life-scene-cv-advisor` | GitHub 仓库，全小写、连字符 |
| **技能名（frontmatter `name`）** | `life-scene-cv-advisor` | 必须与目录名、仓库名**三者一致**，否则 WorkBuddy 加载会找不到入口 |
| **目录名** | `life-scene-cv-advisor/` | 放进任意 skills 目录即可被识别 |
| **分发包** | `life-scene-cv-advisor-v1.0.0.zip` | 版本号打进文件名，避免多版本混淆 |
| **中文名** | 视觉循证生活顾问 | 只用于人类阅读，不进任何路径或 ID |

### 命名规则（后续新技能沿用，保证长期唯一）

```
<domain>-<modality>-<role>
 领域      输入模态    角色
```

- `domain`：`life`（生活）/ `nba`（篮球）/ `doc`（文档）/ `econ`（经济）
- `modality`：`cv`（视觉）/ `text`（文本）/ `table`（结构化）/ `multi`（多模态）
- `role`：`advisor`（给建议）/ `tracer`（画证据链）/ `bench`（评测）/ `radar`（监控）

按此规则，本仓库后续演进的兄弟项目预留名为：

| 预留名 | 用途 |
|---|---|
| `life-cv-tracer` | 把本技能的输出画成证据链可视化图 |
| `life-text-bench` | 用 765 条做 LLM 生活决策评测基准 |
| `life-text-radar` | 政策类条目过期监控 + 版本差分 |
| `nba-cv-tracer` | 主线项目（盖帽分析的时序证据可视化） |

### 唯一性核验（2026-10-20 实测）

- 检索 GitHub、LobeHub Skills、skillsMP、agentskills.codes 四个渠道，**无同名技能**。
- 相近名 `visual-advisor`、`visual-verdict`、`visual-qa` 均属「UI 截图质量评审」领域，与本技能（生活场景 → 循证条目）无交集，不构成混淆。
- **主动回避的名字**（避免与上游或泛名撞车）：
  - ❌ `HowToLiveBetter-*`、`htlb-*`：与上游仓库 `eternity4719/HowToLiveBetter` 混同，且上游已有 `HowToLiveBetter-Kit` 等衍生项目。
  - ❌ `life-advisor`、`life-guide`、`visual-life`：过于宽泛，长期极易重名。
  - ❌ 中文仓库名：不利于 CLI、zip 包名与 frontmatter 字段。

### 版本规范

- 遵循 **SemVer**：`MAJOR.MINOR.PATCH`
  - `PATCH`：改文案、修脚本 bug、补 few-shot 示例
  - `MINOR`：新增场景检查清单、新增检索参数、新增输出字段
  - `MAJOR`：改 frontmatter `name`、改输出契约、换数据源
- 版本号写三处，必须同步：`SKILL.md` frontmatter 的 `version`、本文件顶部徽章与 CHANGELOG、`dist` 包名。

---

## 二、它解决什么问题

上游《高性价比人生指南》已有 **15 个衍生项目**（10 个阅读站、4 个 App/小程序、1 个插件、1 个数据集、漫画版）。它们的共同形态是「**让人更好地读这本书**」。

本技能走的是另一条路：**「让人不用读这本书」** —— 用户不输入关键词，而是**给一张图**；技能负责把图翻译成书里的条目号。

| 维度 | 已有 15 个衍生项目 | 本技能 |
|---|---|---|
| 输入 | 关键词 / 目录浏览 | **图片 + 情境问题** |
| 核心能力 | 检索与排版 | **视觉要素 → 条目映射** |
| 输出 | 条目原文 | **带图证 + 出处的行动清单** |
| 门槛 | 用户要知道自己该查什么 | **用户只需要拍张照** |

一句话差异：**已知该查什么的人，用阅读站；不知道该查什么的人，用这个技能。**

---

## 三、工作原理

```
用户上传图片 + 一句话情境
        │
  ① 危机前置 ── 命中急救/自杀/在办法律程序 → 先给处置，不做性价比排序
        │
  ② 数据就位 ── sync_book.py 增量同步上游正文（失败则降级用本地副本）
        │
  ③ 视觉感知 ── 按 references/visual-checklist.md 逐项读图
        │        只记"亲眼确认"的要素，标注：清晰可见 / 疑似 / 看不出
        │
  ④ 条目检索 ── search_entries.py 取整条（含备注栏的适用边界与争议）
        │
  ⑤ 排序 ── 性价比档（极高>高>一般）→ 证据等级（A>B>C）→ 人群标签命中优先
        │    四种口径（死亡率/金钱/时间/自由）分列，不合成总分
        │
  ⑥ 交付 ── 每条带：第 X 节第 Y 条 + 图中依据 + 动作 + 成本 + 说人话 + 来源
```

对应到 Agent 七层架构（本技能覆盖 4 层）：

| 层 | 本技能的实现 |
|---|---|
| ① 进入层 | 多模态图片输入 + 触发词识别 |
| ② 感知层 | `visual-checklist.md` 的结构化视觉观察协议 |
| ④ 访问层 | `search_entries.py` 对 765 条的过滤检索 |
| ⑤ 决策层 | 排序规则（性价比 → 证据等级 → 人群 → 口径） |
| ⑦ 交付层 | 带出处与证据强度的清单 + 免责声明 |

> 注意：本技能**不训练、不部署任何 CV 模型**。WorkBuddy 主 Agent 自带多模态读图能力，技能的价值在于把「看什么 → 映射到哪条 → 怎么排序」写成确定性协议（prompt + few-shot + rules）。

---

## 四、目录结构

```
life-scene-cv-advisor/
├── SKILL.md                        # 主流程与纪律（102 行）—— 技能入口，Agent 只读这一个
├── README.md                       # 本文件（仓库说明，不参与技能运行）
├── LICENSE                         # 代码部分 MIT
├── scripts/
│   ├── sync_book.py                # 上游正文 git 增量同步（52 行）
│   └── search_entries.py           # 765 条解析 + 多维过滤检索（149 行）
└── references/
    ├── visual-checklist.md         # 视觉→条目映射矩阵（75 行）
    └── few-shot.md                 # 4 个示例，含 1 个反面教材（68 行）
```

**文件职责**

| 文件 | 谁读 | 作用 |
|---|---|---|
| `SKILL.md` | Agent（自动加载） | 6 步流程 + 5 条纪律 + 输出模板。改行为改这里 |
| `scripts/sync_book.py` | Agent 调用 | 有目录就 `git pull --ff-only`，没有就 `git clone --depth 1`，输出 HEAD 日期 |
| `scripts/search_entries.py` | Agent 调用 | 自包含解析器（零第三方依赖），支持 7 个过滤参数 + JSON 输出 |
| `references/visual-checklist.md` | Agent 按需读 | 6 类场景（厨房/卫浴/全屋/文件截图/户外/人物）的检查项 → 节条号对照表 |
| `references/few-shot.md` | Agent 按需读 | 回答骨架与口吻；示例 3 明确「哪些话不能编」 |

---

## 五、安装

### 方式 A：目录拷贝（推荐）

```bash
# WorkBuddy 用户级（Windows 示例；C 盘 junction 指向 E 盘亦可）
cp -r life-scene-cv-advisor ~/.workbuddy/skills/

# 其他 Agent Skills 生态
cp -r life-scene-cv-advisor .claude/skills/
```

放进去就会在被识别，无需注册、无需重启。

### 方式 B：解压分发包

```bash
unzip life-scene-cv-advisor-v1.0.0.zip -d ~/.workbuddy/skills/
```

### 方式 C：显式调用

在对话中输入 `/life-scene-cv-advisor`，或直接发图说「帮我看看这个厨房/药箱/这份合同」。

---

## 六、依赖与环境

| 项 | 要求 |
|---|---|
| Python | **3.9+**（仅标准库：argparse / json / os / re / sys / pathlib，**零 pip 依赖**） |
| git | 可选，仅 `sync_book.py` 需要（无 git 时手动下载正文亦可） |
| 宿主 | 支持 Agent Skills 规范 + 多模态读图的客户端（WorkBuddy / Claude Code 等） |

### 数据源准备

技能本身**不含**《高性价比人生指南》正文（那是上游 CC BY 4.0 内容，不打包进本仓库），首次使用需拉取：

```bash
python scripts/sync_book.py                 # 默认 E:/Projects/HowToLiveBetter
python scripts/sync_book.py --src D:/hltb   # 指定目录
```

**路径优先级：`--src` > 环境变量 `HTLB_SRC` > 脚本顶部 `DEFAULT_SRC` 常量。**

跨平台建议设一次环境变量，之后脚本与 SKILL.md 都不用改：

```bash
# Windows PowerShell
[Environment]::SetEnvironmentVariable("HTLB_SRC", "D:\hltb", "User")

# macOS / Linux
echo 'export HTLB_SRC="$HOME/data/HowToLiveBetter"' >> ~/.zshrc
```

非 Windows 用户另需把 `SKILL.md` 第 1 步、第 3 步里示例命令的路径换成自己的（其余逻辑与平台无关）。

---

## 七、使用方法

### search_entries.py 参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `--query` | 关键词，空格分隔，**任一命中即算**，按命中数排序 | `--query 燃气 软管` |
| `--section` | 只看第 N 节（1–34） | `--section 34` |
| `--grade` | 只看证据等级 `A` / `B` / `C` | `--grade A` |
| `--audience` | 只看适用人群（97 条带此标签） | `--audience 老人` |
| `--ratio` | 只看性价比档 `极高` / `高` / `一般` | `--ratio 极高` |
| `--max` | 最多几条（默认 8） | `--max 3` |
| `--json` | 结构化输出，供程序消费 | `--json` |
| `--src` | 指定书库目录 | `--src D:/hltb` |

参数可叠加：

```bash
python scripts/search_entries.py --query 药 过期 --audience 老人 --ratio 极高 --max 3
```

无命中时的兜底：直接 `grep -rn "关键词" <书库>/book/`，仍无命中就归入「书里没写」——**不允许用常识冒充条目**。

### 输出契约

```
看了你的图，先说结论 + 图中确认的 N 个要素（1 句话）。

【先做】◆ 第 X 节第 Y 条（节名）｜性价比档｜证据等级
- 图中依据：你在图里看到了什么
- 动作：动词开头，一句话
- 成本：照抄条目
- 说人话：照抄条目（RR/OR 已在条目里翻成中文）
- 来源：首个原始出处
- 备注要点（适用边界/争议，如有）

【可以做】次优先条目，同格式，可精简

【图中看不出】2-3 个图中无法判断但值得自查的点，指到对应节条号

——仅供参考，不替代医生/律师/会计；数据同步至 YYYY-MM-DD（CC BY 4.0，出处：高性价比人生指南）
```

### 五条硬纪律

1. **图中没看到的不说** —— 「看不出」就进「图中看不出」清单，禁止脑补。
2. **书里没有的不编** —— 常识可以补，但必须标注「这是常识，不是书里的条目」。
3. **数字照抄一个不改** —— RR/OR 就地译成日常话，原值保留在括号里。
4. **政策类带截至日期** —— 金额、时限、名单照抄书上标注的日期，并提醒以官方渠道为准。
5. **争议必须带反方** —— 88 条标了「争议」的条目，必须同时给出反方证据。

---

## 八、数据说明（实测，非转述）

| 指标 | 实测值 |
|---|---|
| 条目总数 | **765** |
| 节数 | **34** |
| 证据等级 | A **495** / B **218** / C **52** |
| 性价比档 | 极高 **122** / 高 **344** / 一般 **299** |
| 口径分布 | 金钱 290 / 死亡率 274 / 自由 124 / 时间 77 |
| 人群标签 | 97 条（婴幼儿 29 / 怀孕 22 / 孩子 21 / 老人 14 / 35岁 5 / 女性 3 / 女性+35岁 3） |
| 争议标注 | **88** 条 |
| 字段解析成功率 | **100%**（765/765，与上游 README 官方统计逐一吻合） |
| 上游 HEAD | `2026-10-15`（`5f210ca`） |

每条 6 个固定字段（成本 / 说人话 / 收益 / 证据等级 / 来源 / 备注）+ 5 个机器可读枚举标签（钱 / 时间 / 毅力 / 收益 / 口径 / 人群，藏在 HTML 注释里）。性价比档算法与上游 `index.html` 一致（收益量级 + 钱/时间/毅力三项成本分）。

---

## 九、局限性（请如实告知用户）

1. **视觉误判**：光线、角度、分辨率都会影响识别，安全类结论必须标「疑似，请自行确认」。
2. **不替代专业意见**：不替代医生、律师、会计；具体病情/案件/税务只给方向和该找谁。
3. **观点归属**：性价比档与证据等级是**原作者的判断**，输出时以「书里的说法」呈现，不冒充客观事实。
4. **隐私**：一次分析只针对用户上传的图，不主动索取更多隐私照片。
5. **时效性**：政策类条目会过期，答复必须带「数据同步至 YYYY-MM-DD」。

---

## 十、许可证与署名

**分两层，不要搞混：**

| 内容 | 许可 |
|---|---|
| 本仓库的 **SKILL.md / scripts / references**（本仓库原创） | **MIT**（见 `LICENSE`） |
| 《高性价比人生指南》**正文数据**（本仓库不打包，运行时从上游拉取） | **CC BY 4.0**，著作权归原作者 |

使用、改编、再分发正文时，**四件事一个都不能少**：

1. **署名** —— 注明原作者与项目名《高性价比人生指南》
2. **许可链接** —— 附上 CC BY 4.0 链接
3. **标注改动** —— 说明你对原文做了哪些修改
4. **标注同步日期** —— 说明数据取自哪一天的上游版本

> 合规提示：本仓库不 vendored 上游正文，只提供拉取脚本，正是为了让「数据许可」与「代码许可」保持清晰边界。

---

## 十一、更新与维护

### 同步上游内容

```bash
python scripts/sync_book.py        # 正文更新后重跑即可，条目变动自动生效
```

上游每周更新，建议每月同步一次；同步后 `search_entries.py` 无需改动（解析器按 Markdown 结构工作，不依赖条号硬编码）。

### 后续更新记在哪里

| 改了什么 | 改哪个文件 | 版本怎么升 |
|---|---|---|
| 回答口吻、示例 | `references/few-shot.md` | PATCH |
| 新增场景检查项 | `references/visual-checklist.md` | MINOR |
| 新增检索维度 | `scripts/search_entries.py` | MINOR |
| 改流程/排序/纪律 | `SKILL.md` | MINOR 或 MAJOR |
| 改输出契约 | `SKILL.md` + 本文件输出契约章节 | MAJOR |
| 改 `name` | `SKILL.md` frontmatter（**同时改仓库名与目录名**） | MAJOR |

每次发版：更新 `SKILL.md` 的 `version` → 追加 CHANGELOG → 打 tag `v1.0.0` → 重新打包 zip。

### CHANGELOG

| 版本 | 日期 | 变更 |
|---|---|---|
| **1.0.0** | 2026-10-20 | 首个公开版本。`SKILL.md` 六步流程 + 危机前置；`sync_book.py` 增量同步；`search_entries.py` 七参数检索 + JSON 输出；`visual-checklist.md` 六类场景映射；`few-shot.md` 四示例（含借条反面教材）。数据源路径支持 `--src` / `HTLB_SRC` 环境变量。实测 765 条解析成功率 100%。 |

### 路线图

- **v1.1**：补充「装修现场 / 车内 / 食品标签」三类场景检查清单；`--lens` 按口径过滤
- **v1.2**：输出端接 `life-cv-tracer`，把「第 X 节第 Y 条 → 证据 → 原始文献」画成证据链图
- **v2.0**：人格化为「循证人生顾问」专家（expert-manager 转化），积累的 few-shot 即训练数据
- **v3.0**：MCP Server 化，跨 Cursor / Claude Code 分发，向上游 `衍生项目.md` 提 PR 收录

---

## 十二、致谢与上游

- 数据与灵感来源：[eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) —— 《高性价比人生指南》，正文 CC BY 4.0。
- 本技能是独立衍生项目，与上游作者无隶属关系；条目内容以书为准，使用风险由使用者自担。

---

**维护者注**：本文件随版本更新，任何对外发布前请确认「版本号三处一致」（SKILL.md / README 徽章+CHANGELOG / zip 包名）。
