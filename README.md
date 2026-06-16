# IDE 初始化脚本使用说明

将 `agents/` 共享配置一键映射到 Cursor / Trae / Codex / OpenCode / Claude / IDEA 等多种 IDE。

---

## 脚本列表

| 脚本 | 用途 |
|------|------|
| `scripts/init-env.py` | 从 `env.json` / 系统环境变量生成 MCP / Codex / OpenCode 配置 |
| `scripts/init-ide.py` | 通用初始化（支持多 IDE 选择） |
| `init-env.cmd` / `init-env.sh` | 一键执行环境初始化 |
| `install.cmd` / `install.sh` | 一键执行环境初始化 + 多 IDE 初始化 |

## 环境要求

- Python 3.10+
- Windows / macOS / Linux 均可
- Windows 下创建 Junction 需以**管理员权限**运行终端

## 核心设计

`agents/rules/` 是**唯一数据源**，各 IDE 的 `rules/` 目录通过 Windows Junction（或软链）指向它，修改一处自动同步。

```
agents/rules/                <-- 唯一数据源（在这里编辑）
  ├── .trae/rules/           <-- Junction（自动同步）
  ├── .cursor/rules/         <-- Junction（自动同步）
  ├── .codex/rules/          <-- Junction（自动同步）
  ├── .claude/rules/         <-- Junction（自动同步）
  └── ...                    <-- 其他 IDE 同理
```

密钥与配置分离：

```
env.json (本地，含真实密钥, 不提交)
  ├──> agents/mcp/mcp.template.json     ──生成──> agents/mcp/mcp.json
  ├──> ide/codex/auth.template.json     ──生成──> ide/codex/auth.json
  └──> ide/opencode/opencode.template.json ──生成──> ide/opencode/opencode.json
```

---

## init-env.py（环境/密钥初始化）

### 工作流程

1. 读取 `env.json` 中配置的密钥
2. **若某项为空，自动回退使用 OS 环境变量**
3. 设置进程或用户级环境变量
4. 用密钥替换以下模板中的 `${KEY}` 占位符：
   - `agents/mcp/mcp.template.json` → `agents/mcp/mcp.json`
   - `ide/codex/auth.template.json` → `ide/codex/auth.json`
   - `ide/opencode/opencode.template.json` → `ide/opencode/opencode.json`

### 基本用法

```bash
# 默认：设置进程环境变量 + 生成所有配置文件
python scripts/init-env.py

# 仅设置环境变量（不生成配置文件）
python scripts/init-env.py -a Env

# 仅生成配置文件
python scripts/init-env.py -a Generate

# 写入用户级环境变量（持久化，跨终端有效）
python scripts/init-env.py -a Env --scope user --force

# 输出 export 语句供 shell 直接 eval
python scripts/init-env.py -a ExportShell
```

### 参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--action` | `-a` | `Env` / `Generate` / `All` / `ExportShell` | `All` |
| `--env-file` | `-f` | 密钥配置文件路径 | `env.json` |
| `--template-file` | — | MCP 模板路径 | `agents/mcp/mcp.template.json` |
| `--output-file` | — | MCP 生成路径 | `agents/mcp/mcp.json` |
| `--scope` | — | `process` / `user` | `process` |
| `--force` | — | 跳过确认提示 | 否 |

### 首次配置

```bash
# 1. 复制密钥模板
cp env.example.json env.json

# 2. 编辑 env.json 填入真实密钥
#    没填的字段会自动从 OS 环境变量读取

# 3. 运行初始化
python scripts/init-env.py -a All
```

### 密钥清单

| 变量名 | 用途 |
|--------|------|
| `OPENAI_API_KEY` | OpenAI / Codex / OpenCode |
| `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` | Anthropic / Claude |
| `AMAP_MAPS_API_KEY` | 高德地图 MCP |
| `WECOM_WEBHOOK_URL` | 企业微信 |
| `BOSS_COOKIE` / `BOSS_BST` | BOSS 直聘 |
| `TAVILY_API_KEY` | Tavily 搜索 |
| `FIRECRAWL_API_KEY` | Firecrawl 爬虫 |
| `YUQUE_TOKEN` | 语雀 |
| `STITCH_API_KEY` | Stitch 原型 |
| `MASTERGO_MAGIC_TOKEN` | MasterGo Magic |
| `CONTEXT7_API_KEY` | Context7 文档 |

### 版本控制边界

| 文件 | 提交？ | 说明 |
|------|--------|------|
| `env.example.json` | ✅ | 仅占位，可安全提交 |
| `env.json` | ❌ | 含真实密钥（已在 `.gitignore`） |
| `*.template.json` | ✅ | 仅 `${KEY}` 占位符 |
| `agents/mcp/mcp.json` | ❌ | 由脚本生成（已忽略） |
| `ide/codex/auth.json` | ❌ | 由脚本生成（已忽略） |
| `ide/opencode/opencode.json` | ❌ | 由脚本生成（已忽略） |

---

## init-ide.py（通用 IDE 初始化）

### 基本用法

```bash
# 默认：初始化所有支持的 IDE，写到当前用户主目录
python scripts/init-ide.py

# 强制覆盖已有配置
python scripts/init-ide.py -f

# 仅初始化指定 IDE
python scripts/init-ide.py -i Cursor
python scripts/init-ide.py -i Trae
python scripts/init-ide.py -i trae-cn
python scripts/init-ide.py -i trae-solo-cn
python scripts/init-ide.py -i Codex
python scripts/init-ide.py -i Claude
python scripts/init-ide.py -i WorkBuddy
python scripts/init-ide.py -i Qoder
python scripts/init-ide.py -i OpenClaw
python scripts/init-ide.py -i OpenCode
python scripts/init-ide.py -i IDEA
python scripts/init-ide.py -i Agents

# 指定目标目录
python scripts/init-ide.py -i trae-cn -t $env:USERPROFILE -f
python scripts/init-ide.py -t D:\my-project

# 指定源目录（agents/ 所在目录）
python scripts/init-ide.py --source-dir D:\my-project
```

### 参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--target-dir` | `-t` | 目标项目根目录（IDE 配置写入位置） | 用户主目录 |
| `--source-dir` | `-s` | 源目录（`agents/` 所在目录） | 脚本所在目录的父目录 |
| `--ide` | `-i` | 见下方 IDE 选项 | `All` |
| `--force` | `-f` | 强制覆盖已有配置 | 否 |

### 支持的 IDE

`Cursor` · `Trae` · `trae-cn` · `trae-solo-cn` · `Codex` · `Claude` · `WorkBuddy` · `Qoder` · `OpenClaw` · `OpenCode` · `IDEA` · `Agents` · `All`

### 链接方式概览

| 目标 | 链接类型 | 源 |
|------|----------|-----|
| `.agent/rules/` | Junction（目录） | `agents/rules/` |
| `.trae/rules/` | Junction（目录） | `agents/rules/` |
| `.trae-cn/rules/` | Junction（目录） | `agents/rules/` |
| `.cursor/rules/` | Junction（目录） | `agents/rules/` |
| `.codex/rules/` | Junction（目录） | `agents/rules/` |
| `.claude/rules/` | Junction（目录） | `agents/rules/` |
| `.workbuddy/rules/` 等 | Junction（目录） | `agents/rules/` |
| `.mcp.json` / `*/mcp.json` | Symlink/Copy（文件） | `agents/mcp/mcp.json` |
| `.cursor/mcp.json` | 生成文件 | `agents/mcp/mcp.json`（mcpServers 键） |
| `.codex/config.toml` | 生成文件 | `agents/mcp/mcp.json`（TOML 格式） |
| `.opencode/opencode.json` | 生成文件 | `ide/opencode/opencode.template.json` |
| `*/skills/` | 复制目录 | `agents/skills/` |
| `*/skills/README.md` | 生成文件 | 技能索引 |

---

## 一键脚本

### 仅生成密钥相关配置

```bash
# Windows
.\init-env.cmd

# macOS / Linux
./init-env.sh
```

等价于 `python scripts/init-env.py -a Generate`。

### 全量初始化（环境 + 多 IDE）

```bash
# Windows
.\install.cmd

# macOS / Linux
./install.sh
```

依次执行：

1. `init-env`（生成 mcp.json / auth.json / opencode.json）
2. `init-ide -i Agents`
3. `init-ide -i trae-cn`
4. `init-ide -i Cursor`
5. `init-ide -i Codex`
6. `init-ide -i OpenCode`
7. `init-ide -i IDEA`
8. `init-ide -i trae-solo-cn`

---

## 生成的目录结构

```
项目根目录/
├── agents/                            # 唯一数据源
│   ├── rules/                         # Rules（编辑这里）
│   │   ├── git-commit-message.md
│   │   ├── api/collaboration-standards.md
│   │   ├── backend/{coding,database,ddd}-standards.md
│   │   ├── design/standards.md
│   │   ├── frontend/coding-standards.md
│   │   ├── product/prd-standards.md
│   │   ├── security/standards.md
│   │   └── testing/standards.md
│   ├── mcp/
│   │   ├── mcp.template.json          # MCP 模板（提交）
│   │   ├── mcp-env.template.json      # 密钥模板（提交）
│   │   └── mcp.json                   # 由 init-env 生成（不提交）
│   └── skills/*/SKILL.md              # 技能定义
│
├── ide/
│   ├── codex/
│   │   ├── auth.template.json         # 提交
│   │   ├── auth.json                  # 由 init-env 生成（不提交）
│   │   └── config.toml
│   ├── opencode/
│   │   ├── opencode.template.json     # 提交
│   │   └── opencode.json              # 由 init-env 生成（不提交）
│   └── idea/
│       └── acp.json
│
├── .trae/rules/                       --Junction--> agents/rules/
├── .cursor/rules/                     --Junction--> agents/rules/
├── .codex/rules/                      --Junction--> agents/rules/
├── .mcp.json                          --Symlink---> agents/mcp/mcp.json
├── .cursor/mcp.json                   （生成，mcpServers 键）
├── .codex/config.toml                 （生成，TOML）
├── .opencode/opencode.json            （生成，OpenCode）
├── env.json                           （本地密钥，不提交）
├── env.example.json                   （密钥模板，可提交）
├── AGENTS.md                          （Trae 项目指令）
└── scripts/
    ├── init-env.py
    └── init-ide.py
```

---

## 不同 IDE 的格式差异

| 项目 | Cursor | Trae | Codex | OpenCode |
|------|--------|------|-------|----------|
| MCP 键名 | `mcpServers` | `mcpServers` | TOML 表 | `mcp` |
| MCP 位置 | `.cursor/mcp.json` | `.mcp.json` | `.codex/config.toml` | `.opencode/opencode.json` |
| Rules 目录 | `.cursor/rules/` | `.trae/rules/` | `.codex/rules/` | `.opencode/skills/` |
| Rules 扩展名 | `.mdc` | `.md` | `.md` | — |
| 项目指令 | — | `AGENTS.md` | — | — |

---

## 推荐 Skill 列表（按角色）

> 角色映射由 [`doc/skills-mapping.csv`](file:///c:/Users/59300/Desktop/agent-init-plugin/doc/skills-mapping.csv) 驱动，脚本运行时自动读取。新增/调整 Skill 只需修改 CSV 即可，无需改代码。

### CSV 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `skill_name` | Skill 名称（与 `agents/skills/` 目录名一致） | `drawio-skill` |
| `category` | 功能分类 | `可视化` |
| `role` | 适用角色（`\|` 分隔） | `Frontend\|Backend\|Design` |
| `description` | 功能简述 | `生成 .drawio 流程图/架构图...` |
| `trigger_keywords` | 触发关键词（`\|` 分隔） | `画图\|流程图\|架构图` |
| `installable` | 是否为通用安装型技能 | `true` / `false` |

- **内置技能**（`installable: false`）：按角色直接推荐，开箱即用
- **通用安装型技能**（`installable: true`）：通过 `find-skills` 安装后使用

### 前端（Frontend）

| Skill | 说明 |
|-------|------|
| `stitch-prototype-skill` | 用 Stitch MCP 从文本生成 UI 原型 |
| `mastergo-magic-skill` | 用 MasterGo Magic 生成中保真原型与前端代码 |
| `drawio-skill` | 生成 .drawio 流程图、架构图 |
| `mermaid-sequence-from-flow` | 业务流程转 Mermaid 序列图 |

### 后端（Backend）

| Skill | 说明 |
|-------|------|
| `restful-api-design-skill` | RESTful API 设计、规范自检、OpenAPI 生成 |
| `task-plan-skill` | PRD 拆解任务计划（里程碑、依赖、风险） |
| `drawio-skill` | 架构图、服务关系图、ER 图 |

### 设计（Design）

| Skill | 说明 |
|-------|------|
| `stitch-prototype-skill` | 快速出原型方案、迭代 |
| `mastergo-magic-skill` | MasterGo 设计稿到代码协作 |
| `prd-to-mastergo-interaction-skill` | PRD 转 MasterGo 交互原型 |
| `drawio-skill` | 用户旅程、信息架构、页面流程 |

### 产品（Product）

| Skill | 说明 |
|-------|------|
| `usecase-prd-skill` | 用例化 PRD（动作→响应→验收） |
| `task-plan-skill` | 任务拆解与排期 |
| `weekly-report-skill` | 周报 / 月报结构化输出 |
| `prd-to-mastergo-interaction-skill` | 推动需求向交互稿过渡 |

### 通用安装型技能

| Skill | 分类 | 说明 |
|-------|------|------|
| `find-skills` | 技能发现 | 在仓库中查找适合当前任务的技能 |
| `personnel-recruitment` | 人力资源 | 结构化招聘（JD、简历、面试） |
| `hardware-agent-prompt-skill` | 硬件 AI | 硬件智能体提示词与人格设定 |
| `elon-musk-perspective` | 思维模型 | 第一性原理、白痴指数、五步算法 |

---

## 常见问题

### Q: 为什么有 `[WARN] Unresolved placeholders ...`？

`env.json` 中对应键的值为空，且 OS 环境变量也未设置。处理方式：

1. 在 `env.json` 填入真实值；或
2. `setx OPENAI_API_KEY xxx`（Windows） / `export OPENAI_API_KEY=xxx`（*nix）后重跑；或
3. 若该占位符不再需要，从模板中移除（如已弃用的 OpenICU / OpenRouter）。

### Q: 提示 "需要管理员权限"？

Windows 下 Junction 创建需要管理员权限。右键终端 → "以管理员身份运行"。

### Q: 已有配置被覆盖了怎么办？

脚本默认不覆盖已有配置。要覆盖，加 `--force` / `-f`。

### Q: 修改 `agents/rules/` 后需要重新运行脚本吗？

不需要。Junction 会自动同步。

### Q: 仅想刷新某个 IDE 的配置？

```bash
python scripts/init-ide.py -i Cursor -f
```
