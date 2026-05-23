# Agent 创建与导入指南

## 第一步：创建四个 Agent

进入 **设置 → 助手**，点击「创建」按钮，依次创建以下四个 Agent：

### 1. 前端工程师

| 设置项 | 值 |
|--------|-----|
| 名称 | `前端工程师` 或 `Frontend` |
| 思维方式 | **Hanako（花子）** |
| 工作目录 | `D:\Hanako\agents\web-review\frontend-engineer` |

### 2. UI/UX设计师

| 设置项 | 值 |
|--------|-----|
| 名称 | `UI/UX设计师` 或 `UX` |
| 思维方式 | **Hanako（花子）** |
| 工作目录 | `D:\Hanako\agents\web-review\ux-designer` |

### 3. 性能优化师

| 设置项 | 值 |
|--------|-----|
| 名称 | `性能优化师` 或 `Performance` |
| 思维方式 | **Ming（鸣）** |
| 工作目录 | `D:\Hanako\agents\web-review\performance-engineer` |

### 4. 安全审计师

| 设置项 | 值 |
|--------|-----|
| 名称 | `安全审计师` 或 `Security` |
| 思维方式 | **Kong（空）** |
| 工作目录 | `D:\Hanako\agents\web-review\security-auditor` |

## 第二步：导入人设（ishiki）

每个 Agent 创建完成后，进入 **设置 → 助手 → 选择该 Agent → 意识（ishiki.md）**，将对应目录下的 `SOUL.md` 文件内容粘贴进去。

| Agent | SOUL.md 路径 |
|-------|-------------|
| 前端工程师 | `D:\Hanako\agents\web-review\frontend-engineer\SOUL.md` |
| UI/UX设计师 | `D:\Hanako\agents\web-review\ux-designer\SOUL.md` |
| 性能优化师 | `D:\Hanako\agents\web-review\performance-engineer\SOUL.md` |
| 安全审计师 | `D:\Hanako\agents\web-review\security-auditor\SOUL.md` |

## 第三步：配置操作规则

每个 Agent 目录下的 `AGENTS.md` 会自动被 Hanako 读取（放在工作目录下即可生效）。

如果想额外确认：进入 Agent 设置，将 `AGENTS.md` 内容追加到操作规则中。

## 第四步：创建团队协作频道

进入左侧边栏 **频道 Tab**，创建一个新群组，把四个 Agent 都加进来。

频道名称建议：`🔍 网页审查室`

## 第五步：开始审查

在频道中 @ 所有成员，发送你要审查的 HTML 代码（或直接贴链接），四位专家会各自从自己的领域给出审查报告。

你也可以直接在自己的主对话中：
- `@前端工程师 帮我看看这段 HTML 的语义结构`
- `@安全审计师 扫描这个表单页面有没有漏洞`

## 审查工作流建议

一次完整的审查流程：

```
你：请四位帮我审查这个页面 [贴代码]

前端工程师 → 结构、语义、代码质量
UI/UX设计师 → 视觉设计、用户体验
性能优化师 → 加载性能、资源优化
安全审计师 → 安全漏洞、攻击面

你根据四份报告决定修什么、怎么修
```

如果你希望按顺序审查（先修代码再调设计再看性能最后查安全），逐个 @ 对应 Agent 即可。
