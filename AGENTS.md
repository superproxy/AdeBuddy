# AGENTS.md

## 1. 项目定位

这是一个面向公司内部 **前端、后端、设计、产品** 人员使用的 AI 智能体工程仓库，核心资产包括：

- **技能库**：`agents/skills/*/SKILL.md`
- **MCP 配置参考**：`agents/mcp/mcp_config.yaml`
- **本地运行态 MCP 配置**：`agents/mcp/mcp.json`
- **MCP 指令说明**：`agents/mcp/mcp-codex.md`

本文件作为仓库级总入口，负责定义：

- 角色如何选择
- Git 管理和协作边界
- Rules 规则
- MCP 推荐使用方式
- Skills 推荐矩阵

> 说明：当前以本仓库已有结构为主进行治理整理。若后续需要严格适配 Trae 的 Rules / MCP / Skills 官方格式，请再按官方文档补齐语法细节；不要在未验证前提下臆造官方字段。

---

## 2. 指令优先级与使用方式

### 指令优先级

1. 当前任务的用户明确要求
2. 本文件（`AGENTS.md`）中的仓库级规则
3. 角色模板：`templates/agents/*.txt`
4. 技能说明：`agents/skills/*/SKILL.md`

### 使用原则

- 优先复用已有模板、skills、MCP 组织方式，不随意新建平行体系。
- `AGENTS.md` 只负责**顶层治理与路由**，不复制角色长提示词与 skill 详细执行步骤。
- 需要详细角色能力时，回到对应模板；需要详细技能流程时，回到对应 `SKILL.md`。

---

## 3. Git 管理规则

### 基本原则

- 修改范围只聚焦当前任务，避免无关重构。
- 优先修改已有文件，避免新增重复文档或平行配置。
- 新增规则、说明、映射时，尽量保持短小、可扫描、可审查。
- 提交内容必须适合团队协作，不把本机临时状态当成共享规范。

### 禁止提交的内容

- Token、API Key、Cookie、账号密钥
- 带敏感参数的 MCP 配置
- 本机绝对路径、个人环境变量值
- 临时导出文件、调试日志、无说明的生成物

### MCP 相关 Git 边界

- `config/mcp_config.yaml` 用于表达**共享参考结构**。
- `.mcp.json` 属于**本地运行态配置**，可能包含密钥或机器相关参数。
- 不要把 `.mcp.json` 中的真实密钥、Header、Token 复制到共享文档、模板或提交说明中。
- 当前仓库中旧的 `mcp.json` 已被 `.mcp.json` 替代；后续继续维护时，以“共享结构”和“本地私有配置”分离为原则。

---

## 4. 角色路由

### Product

**适用场景**：需求澄清、PRD、功能拆解、Story、验收标准、范围界定。

**优先复用模板**：`templates/agents/product_manager.txt`

**工作重点**：

- 把业务目标转成可评审的需求文档
- 明确用户故事、交互流程、优先级
- 产出可直接交付设计与开发的需求结构

### Design

**适用场景**：用户流程、界面结构、状态设计、设计系统、原型方案。

**优先复用模板**：`templates/agents/ux_designer.txt`

**工作重点**：

- 基于需求设计用户流程和关键界面
- 覆盖空态、错误态、加载态、权限态等关键状态
- 产出可供评审和开发衔接的原型/交互说明

### Frontend

**适用场景**：页面实现、组件拆分、状态管理、接口联调、设计落地。

**说明**：仓库当前没有独立的 `frontend` 角色模板；前端工作默认综合参考设计模板与前端相关 skills。

**工作重点**：

- 关注组件边界、页面状态、交互反馈、接口依赖
- 优先保证设计稿、原型、接口契约三者一致
- 输出要便于工程落地，而不是只停留在视觉描述

### Backend

**适用场景**：API 设计、服务端实现、数据库建模、集成、测试。

**优先复用模板**：`templates/agents/backend_dev.txt`

**工作重点**：

- 关注 RESTful API、业务逻辑、数据结构
- 明确鉴权、错误模型、日志监控、测试建议
- 输出可直接用于研发与联调

### Architect（跨角色补充）

**适用场景**：跨前后端/产品/设计的系统边界、架构取舍、迁移方案。

**优先复用模板**：`templates/agents/architect.txt`

---

## 5. Rules 规则

### 5.1 Product Rules

- 需求默认按 **用户动作 -> 系统响应 -> 验收标准** 组织。
- 必须明确：范围边界、假设、待确认项、不做项。
- 默认给出 **P0 / P1 / P2** 优先级。
- 需求输出要能直接衔接设计和开发，避免只写抽象目标。

### 5.2 Design Rules

- 必须覆盖：`loading / empty / error / permission / offline` 等关键状态。
- 原型或界面说明要能回溯到需求故事和关键流程。
- 默认考虑多端适配、可访问性、一致性。
- 优先描述“用户如何完成任务”，而不是只描述页面长相。

### 5.3 Frontend Rules

- 默认输出组件边界、页面状态、交互反馈、接口依赖。
- 至少补齐：`loading / empty / error / success` 四类状态。
- 优先组件复用、模块分层、低耦合实现。
- 不擅自扩展接口语义；与设计和后端契约保持一致。

### 5.4 Backend Rules

- 优先做 RESTful 资源建模，而不是动作堆叠。
- 明确状态码、错误结构、鉴权、分页、过滤、排序。
- 输出建议包含：API 文档、数据结构、测试建议。
- 默认考虑日志、监控、容错、安全与合规。

---

## 6. MCP 推荐与配置说明

### 6.1 使用原则

- 优先按本仓库现有 MCP 组织方式接入。
- 仓库级共享参考优先看：`config/mcp_config.yaml`
- 本地真实可运行配置优先看：`.mcp.json`
- 若需适配 Trae，请按官方文档补齐语法细节，不在本仓库中伪造未证实的官方格式。

### 6.2 推荐 MCP 按角色映射

| 角色 | 推荐 MCP | 典型用途 |
| --- | --- | --- |
| Frontend | `context7` | 查开发文档、框架/库上下文 |
| Frontend | `stitch` | 快速生成页面原型 |
| Frontend | `mastergo-magic-mcp` | 设计稿/原型到实现协作 |
| Frontend | `drawio` | 模块结构图、流程图 |
| Frontend | `mermaid` | 序列图、状态图、用户流程图 |
| Backend | `context7` | 查开发文档、依赖用法 |
| Backend | `yuque-mcp` | 读写知识库、接口说明、协作文档 |
| Backend | `drawio` | 架构图、数据流图 |
| Backend | `mermaid` | 时序图、状态图、流程图 |
| Design | `stitch` | 界面原型生成 |
| Design | `mastergo-magic-mcp` | MasterGo 相关设计流程 |
| Design | `drawio` | 信息架构、用户流程可视化 |
| Design | `mermaid` | 交互流程、状态说明 |
| Design | `yuque-mcp` | 设计说明沉淀与共享 |
| Product | `yuque-mcp` | PRD、协作文档、知识沉淀 |
| Product | `stitch` | 需求快速转原型 |
| Product | `mastergo-magic-mcp` | PRD 到交互设计协作 |
| Product | `drawio` | 业务流程图、依赖图 |
| Product | `mermaid` | 用户流程、状态流程 |

### 6.3 配置边界

- **共享层**：描述“推荐接什么 MCP、分别做什么事、角色如何映射”。
- **本地层**：保存真实地址、密钥、Header、凭据。
- 文档中只放占位符和说明，不放真实值。

---

## 7. Skills 推荐矩阵

### 7.1 Frontend 推荐 Skills

| Skill | 典型用途 |
| --- | --- |
| `stitch-prototype-skill` | 快速生成界面原型与页面方案 |
| `mastergo-magic-skill` | 设计稿/原型到实现协作 |
| `drawio-skill` | 界面流程、模块关系、说明图 |
| `mermaid-sequence-from-flow` | 把流程转为序列图/交互图 |
| `design-taste-frontend` | 提升 UI 审美质量与设计品味 |
| `high-end-visual-design` | 高端视觉表现与页面设计 |
| `redesign-existing-projects` | 已有项目页面重构与改进 |
| `ui-ux-pro-max` | 强化 UX 设计规范与交互一致性 |

### 7.2 Backend 推荐 Skills

| Skill | 典型用途 |
| --- | --- |
| `restful-api-design-skill` | RESTful API 设计与接口契约 |
| `task-plan-skill` | 开发拆解、里程碑与实施计划 |
| `drawio-skill` | 服务关系图、流程图、架构图 |

### 7.3 Design 推荐 Skills

| Skill | 典型用途 |
| --- | --- |
| `stitch-prototype-skill` | 原型生成 |
| `mastergo-magic-skill` | MasterGo 相关设计流程 |
| `prd-to-mastergo-interaction-skill` | 从 PRD 到交互原型 |
| `drawio-skill` | 用户流程与信息架构可视化 |
| `design-taste-frontend` | 提升 UI 审美质量与设计品味 |
| `high-end-visual-design` | 高端视觉表现与页面设计 |
| `ui-ux-pro-max` | 强化 UX 设计规范与交互一致性 |

### 7.4 Product 推荐 Skills

| Skill | 典型用途 |
| --- | --- |
| `usecase-prd-skill` | 从需求到 PRD |
| `task-plan-skill` | 任务分解与排期 |
| `weekly-report-skill` | 周报/月报结构化输出 |
| `prd-to-mastergo-interaction-skill` | 推动需求向交互稿过渡 |

### 7.5 通用 Skills

| Skill | 典型用途 |
| --- | --- |
| `find-skills` | 技能发现与推荐，帮助用户找到适合当前任务的技能 |
| `personnel-recruitment` | 结构化招聘（JD 优化、简历筛选、面试设计） |
| `hardware-agent-prompt-skill` | 硬件 AI 智能体提示词与角色设定 |
| `elon-musk-perspective` | 马斯克思维模型分析（第一性原理、五步算法等） |

---

## 8. 详细资料入口


### 技能目录

- `agents/skills/find-skills/SKILL.md`
- `agents/skills/stitch-prototype-skill/SKILL.md`
- `agents/skills/mastergo-magic-skill/SKILL.md`
- `agents/skills/prd-to-mastergo-interaction-skill/SKILL.md`
- `agents/skills/restful-api-design-skill/SKILL.md`
- `agents/skills/task-plan-skill/SKILL.md`
- `agents/skills/usecase-prd-skill/SKILL.md`
- `agents/skills/weekly-report-skill/SKILL.md`
- `agents/skills/drawio-skill/SKILL.md`
- `agents/skills/mermaid-sequence-from-flow/SKILL.md`
- `agents/skills/personnel-recruitment/SKILL.md`
- `agents/skills/hardware-agent-prompt-skill/SKILL.md`
- `agents/skills/elon-musk-perspective/SKILL.md`
- `agents/skills/design-taste-frontend/SKILL.md`
- `agents/skills/high-end-visual-design/SKILL.md`
- `agents/skills/redesign-existing-projects/SKILL.md`
- `agents/skills/ui-ux-pro-max/SKILL.md`

### MCP 参考

- `agents/mcp/mcp_config.yaml`
- `agents/mcp/mcp.json`（本地运行态，注意敏感信息）
- `agents/mcp/mcp-codex.md`（本地/外部工具接入说明）

---

## 9. 维护约定

- 角色有新增或调整时，优先更新对应模板，再回到 `AGENTS.md` 更新路由摘要。
- Skill 新增时，优先保持与现有 `SKILL.md` 一致的结构风格。
- MCP 新增时，先判断它属于“共享参考”还是“本地私有配置”，再决定写入哪个文件。
- 若后续补齐 Trae 官方语法适配，应在不破坏当前仓库共享结构的前提下增量调整。
