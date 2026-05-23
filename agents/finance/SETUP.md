# Agent 创建与导入指南

## 第一步：创建 Agent

进入 **设置 → 助手**，点击「创建」按钮，依次创建以下四个 Agent：

### 1. 宏观策略师

| 设置项 | 值 |
|--------|-----|
| 名称 | `宏观策略师` 或 `Macro` |
| 思维方式 | **Hanako（花子）** |
| 工作目录 | `D:\Hanako\agents\finance\macro-strategist` |

### 2. 行业研究员

| 设置项 | 值 |
|--------|-----|
| 名称 | `行业研究员` 或 `Industry` |
| 思维方式 | **Hanako（花子）** |
| 工作目录 | `D:\Hanako\agents\finance\industry-researcher` |

### 3. 量化分析师

| 设置项 | 值 |
|--------|-----|
| 名称 | `量化分析师` 或 `Quant` |
| 思维方式 | **Ming（鸣）** |
| 工作目录 | `D:\Hanako\agents\finance\quant-analyst` |

### 4. 交易纪律官

| 设置项 | 值 |
|--------|-----|
| 名称 | `交易纪律官` 或 `Trading` |
| 思维方式 | **Kong（空）** |
| 工作目录 | `D:\Hanako\agents\finance\trading-disciplinarian` |

## 第二步：导入人设（ishiki）

每个 Agent 创建完成后，进入 **设置 → 助手 → 选择该 Agent → 意识（ishiki.md）**，将对应目录下的 `SOUL.md` 文件内容粘贴进去。

## 第三步：配置操作规则

将每个 Agent 目录下的 `AGENTS.md` 文件内容，可以通过以下方式生效：
- 放到对应 Agent 工作目录下（Hanako 会自动读取）
- 或者粘贴到 Agent 设置中

## 第四步：配置技能

建议为宏观策略师单独启用「davidweng-investment-persona」技能（如果已安装）。

进入 **设置 → 技能 → Agent 技能开关**，选择对应 Agent 后打开需要的技能。

## 第五步：创建团队协作频道

进入左侧边栏 **频道 Tab**，创建一个新群组，把四个 Agent 都加进来。之后你就可以在频道里同时 @ 他们讨论投资问题了。

频道名称建议：`💰 投研作战室`

## 第六步：试运行

切换到宏观策略师 Agent，发一条测试消息：
> "现在的全球经济处于什么周期？A股在这个周期里应该怎么配置？"

当然，你也可以直接在自己的主对话中 @ 其他 Agent 请他们帮忙分析。
