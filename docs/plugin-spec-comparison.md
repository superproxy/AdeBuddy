# 插件规范调研与对齐方案

> 调研日期：2026-07-19
> 调研目标：将 AdeBuddy 自定义 plugin.yaml 格式对齐业界主流规范（Claude Code / Codex CLI / OpenCode / mem0 / VSCode / npm）
> 应用范围：`template/plugins/plugin.schema.yaml`、`template/plugins/*.plugin.yaml`、`server/ai_generator/skills/plugin_*.md`、`scripts/lib/plugins.py`、`frontend/src/stores/pluginBuild.ts`

## 1. 规范来源速查

| 规范 | 清单文件 | 必填字段 | 文档 |
|---|---|---|---|
| **Claude Code** | `.claude-plugin/plugin.json` | `name` | https://code.claude.com/docs/en/plugins-reference |
| **Codex CLI** | `.codex-plugin/plugin.json` | `name` / `version` / `description` / `author.name` / `interface` | https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md |
| **OpenCode** | JS/TS 模块（`~/.config/opencode/plugins/*.ts`） | 无清单，代码注册 | https://opencode.ai/docs/plugins/ |
| **mem0** | 使用 Codex 格式 `.codex-plugin/plugin.json` | 同 Codex | https://docs.mem0.ai/integrations/codex |
| **VSCode 扩展** | `package.json`（with `contributes`） | `name` / `version` / `engines.vscode` / `main` 或 `browser` | https://code.visualstudio.com/api/references/extension-manifest |
| **npm** | `package.json` | `name` / `version` | https://docs.npmjs.com/cli/v10/configuring-npm/package-json |

## 2. Claude Code 插件规范（主要对齐对象）

### 2.1 目录结构

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # 必填：清单
├── commands/                # 可选：slash command（.md）
├── agents/                  # 可选：subagent 定义（.md）
├── skills/                  # 可选：skill 目录（每个含 SKILL.md）
│   └── <skill-name>/SKILL.md
├── hooks/
│   └── hooks.json           # 可选：hook 配置
├── .mcp.json                # 可选：MCP server 配置
├── output-styles/           # 可选：输出样式
├── .lsp.json                # 可选：LSP server 配置
├── themes/                  # 可选：experimental.themes
├── monitors.json            # 可选：experimental.monitors
├── scripts/                 # 可选：hook/utility 脚本
├── LICENSE
├── CHANGELOG.md
└── README.md
```

### 2.2 清单字段（plugin.json）

**必填：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 唯一标识符（kebab-case，无空格） |

**元数据字段：**

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `$schema` | string | JSON Schema URL（编辑器自动补全，运行时忽略） | `"https://json.schemastore.org/claude-code-plugin-manifest.json"` |
| `version` | string | 语义化版本 | `"1.2.0"` |
| `description` | string | 简短说明 | `"Deployment automation tools"` |
| `author` | object | 作者信息 | `{"name": "Dev Team", "email": "dev@company.com"}` |
| `homepage` | string | 文档 URL | `"https://docs.example.com"` |
| `repository` | string | 源码 URL | `"https://github.com/user/plugin"` |
| `license` | string | SPDX 标识 | `"MIT"` / `"Apache-2.0"` |
| `keywords` | array | 发现标签 | `["deployment", "ci-cd"]` |
| `defaultEnabled` | boolean | 默认是否启用（v2.1.154+），缺省 true | `false` |

**组件路径字段（支持 `string|array|object`：路径引用或内联）：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `skills` | string\|array | 自定义 skill 目录，叠加在默认 `skills/` 扫描之上 |
| `commands` | string\|array | 自定义 `.md` 命令文件 |
| `agents` | string\|array | 自定义 agent 文件 |
| `hooks` | string\|array\|object | hook 配置路径或内联 |
| `mcpServers` | string\|array\|object | MCP 配置路径或内联 |
| `outputStyles` | string\|array | 输出样式文件 |
| `lspServers` | string\|array\|object | LSP 配置 |

**扩展字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `userConfig` | object | 启用时提示用户输入的配置项（替代手编 settings.json） |
| `dependencies` | array | 依赖的其他插件（带 semver 约束） `[{name, version}]` |
| `channels` | array | 消息注入通道（Telegram/Slack/Discord 风格） |
| `experimental.themes` | string\|array | 颜色主题（experimental） |
| `experimental.monitors` | string\|array | 后台监视器（experimental） |

**关键行为：未识别字段会被忽略**（仅 `claude plugin validate --strict` 才警告），因此 AdeBuddy 扩展字段 `llm/subagents/rules/commands/envVars/scripts` 在跨 IDE 导出时安全。

### 2.3 路径约定

- 所有路径相对，以 `./` 开头
- `skills`/`hooks`/`mcpServers` 等组件字段是**叠加**在默认扫描之上，不替换默认
- 自定义路径必须遵守 plugin root 命名规则

## 3. Codex CLI 插件规范

### 3.1 清单字段（.codex-plugin/plugin.json）

**必填：** `name` / `version`（严格 semver）/ `description` / `author.name` / `interface`

**顶层字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | kebab-case 标识符 |
| `version` | string | 严格 semver |
| `description` | string | 简短用途 |
| `author` | object | `{name, email, url}` |
| `homepage` | string | 文档 URL |
| `repository` | string | 源码 URL |
| `license` | string | SPDX（如 `MIT`、`Apache-2.0`） |
| `keywords` | array | 搜索/发现标签 |
| `skills` | string | 相对路径，指向 skill 目录/文件 |
| `hooks` | string | hook 配置路径 |
| `mcpServers` | string\|object | MCP 配置路径，或内联对象 |
| `apps` | string | `.app.json` 路径 |
| `interface` | object | UI/UX 元数据块（见下） |

### 3.2 `interface` 字段（Codex 独有，市场展示用）

| 字段 | 类型 | 说明 |
|---|---|---|
| `displayName` | string | 用户可见标题 |
| `shortDescription` | string | 紧凑视图副标题 |
| `longDescription` | string | 详细页长描述 |
| `developerName` | string | 发布者名称 |
| `category` | string | 分类桶（如 `Productivity`、`Coding`） |
| `capabilities` | array | 能力声明（如 `["Interactive", "Write"]`） |
| `websiteURL` | string | 公共网站（绝对 https） |
| `privacyPolicyURL` | string | 隐私政策 URL |
| `termsOfServiceURL` | string | 服务条款 URL |
| `defaultPrompt` | array | 起始 prompt，**最多 3 项**，每项 **≤128 字符** |
| `brandColor` | string | 主题色 hex（如 `#3B82F6`） |
| `composerIcon` | string | composer 图标路径 |
| `logo` | string | logo 资源路径 |
| `logoDark` | string | 暗色模式 logo 路径 |
| `screenshots` | array | 截图路径列表（PNG，存于 `./assets/`） |

### 3.3 验证规则

- `version` 必须严格 semver
- `websiteURL`/`privacyPolicyURL`/`termsOfServiceURL` 必须绝对 `https://`
- `composerIcon`/`logo`/`logoDark`/`screenshots` 必须指向插件包内真实文件
- `apps` 仅在 `.app.json` 实际存在时出现
- `mcpServers` 可指向 `.mcp.json` 或在 `plugin.json` 中内联
- 验证拒绝 `hooks` 等不支持的清单字段（scaffold 会剔除）

### 3.4 marketplace.json（Codex）

```json
{
  "name": "openai-curated",
  "interface": { "displayName": "ChatGPT Official" },
  "plugins": [
    {
      "name": "linear",
      "source": { "source": "local", "path": "./plugins/linear" },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

- 个人插件：`~/.agents/plugins/marketplace.json`
- 仓库/团队插件：`<repo>/.agents/plugins/marketplace.json`
- 每个 plugin entry 必须含 `policy.installation` / `policy.authentication` / `category`

## 4. OpenCode 插件机制（参考）

与 Claude/Codex 不同，OpenCode 走**代码注册**而非清单声明：

- 本地：`.opencode/plugins/*.ts` 或 `~/.config/opencode/plugins/*.ts`（启动时自动加载）
- npm：在 `opencode.json` 中通过 `plugin` 数组声明
  ```json
  { "$schema": "https://opencode.ai/config.json", "plugin": ["opencode-helicone-session"] }
  ```
- npm 包通过 Bun 在启动时安装到 `~/.cache/opencode/node_modules/`
- 插件是 JS/TS 模块，订阅事件、添加工具、修改行为

**对 AdeBuddy 的启示：** OpenCode 不是清单式，导出到 OpenCode 时只能转换为 npm 包或本地 `.ts` 文件，不能直接复用 plugin.yaml。当前策略：导出 skill/MCP/agent 的独立文件到 `~/.config/opencode/` 对应目录即可，不走 plugin 机制。

## 5. mem0 插件模式（Codex 实战样例）

mem0 是跨 IDE 持久化记忆层，在 Codex 上以标准 Codex 插件形式分发：

- 位置：`mem0-plugin/.codex-plugin/plugin.json`
- 三件套：**MCP server**（mem0 cloud） + **lifecycle hooks**（自动捕获/检索记忆） + **SDK skill**（用户调用入口）
- 安装：`codex plugin marketplace add mem0ai/mem0` → `codex plugin add mem0@mem0-plugins`
- 配置：`MEM0_API_KEY` 环境变量

**对 AdeBuddy 的启示：** 这是 `mcpServers + hooks + skills` 组合分发的标准范例，验证了 AdeBuddy 把三者放在同一 plugin.yaml 的设计可行。

## 6. VSCode 扩展规范（参考）

- 清单：`package.json` 中的 `contributes` 字段
- 必填：`name` / `version` / `engines.vscode` / `main`（或 `browser`）
- 关键贡献点：`commands` / `menus` / `configuration` / `views` / `themes`
- 与 Claude/Codex 重叠：`name` / `version` / `description` / `author` / `license` / `keywords` / `homepage` / `repository` / `icon` / `categories`

## 7. npm 生命周期 scripts（scripts 字段对齐对象）

npm 定义的脚本生命周期（按执行顺序）：

| 阶段 | 触发时机 |
|---|---|
| `preinstall` | `npm install` 之前 |
| `install` | `npm install` 期间 |
| `postinstall` | `npm install` 之后 |
| `prepublish` | `npm publish` 之前（仅 npm < 7） |
| `prepare` | `npm install` 之后（devDependencies 装好）+ `npm pack` 之前 |
| `preuninstall` | `npm uninstall` 之前 |
| `uninstall` | `npm uninstall` 期间 |
| `postuninstall` | `npm uninstall` 之后 |

AdeBuddy 的 `scripts` 字段对齐上述生命周期，**旧字段 `init` 等价于 `postinstall`**（向后兼容读取）。

## 8. AdeBuddy 对齐方案

### 8.1 字段对齐矩阵

| AdeBuddy 字段 | 类型 | 来源 | 对齐说明 |
|---|---|---|---|
| `name` | string | Claude/Codex/VSCode | 必填，kebab-case |
| `version` | string | Claude/Codex/VSCode/npm | 必填，semver |
| `description` | string | Claude/Codex/VSCode | 简短说明 |
| `author` | string\|object | Claude/Codex/npm | 兼容简写与 `{name,email,url}` |
| `license` | string | Claude/Codex/VSCode/npm | SPDX 标识（新增） |
| `keywords` | array | Claude/Codex/VSCode/npm | 发现标签（新增） |
| `homepage` | string | Claude/Codex/VSCode/npm | 文档 URL（新增） |
| `repository` | string\|object | Claude/Codex/npm | 源码 URL（新增） |
| `categories` | array | VSCode | 市场归类（新增） |
| `icon` | string | VSCode | 图标路径（新增） |
| `defaultEnabled` | boolean | Claude | 默认启用（新增） |
| `dependencies` | array | Claude | 插件依赖（新增） |
| `userConfig` | object | Claude | 用户配置项（新增） |
| `interface` | object | Codex | UI/UX 元数据（新增，导出 Codex 用） |
| `apps` | string | Codex | App manifest 路径（新增） |
| `manifest_version` | string | AdeBuddy | 清单版本（新增，未来 schema 升级用） |
| `mcpServers` | object | Claude/Codex | 内联 MCP 配置（已有） |
| `skills` | array | Claude/Codex | skill 列表（已有，对象格式） |
| `hooks` | boolean\|object | Claude | hook 配置（已有，类型放宽） |
| `commands` | array | Claude | command 名列表（已有） |
| `subagents` | array | AdeBuddy 扩展 | subagent 角色名（Claude 忽略未识别字段，安全） |
| `rules` | array | AdeBuddy 扩展 | rules 文件路径（同上） |
| `llm` | array | AdeBuddy 扩展 | LLM Provider 配置（同上） |
| `envVars` | object | AdeBuddy 扩展 | 环境变量（同上） |
| `scripts` | object | npm 生命周期 | preinstall/install/postinstall/preuninstall/uninstall/postuninstall/prepare |

### 8.2 scripts 字段迁移对照

| 旧字段 | 新字段 | 说明 |
|---|---|---|
| `scripts.install` | `scripts.install` | 保留（与 npm 一致） |
| `scripts.init` | `scripts.postinstall` | 重命名（向后兼容读取） |
| `scripts.uninstall` | `scripts.uninstall` | 保留 |
| （无） | `scripts.preinstall` | 新增（可选） |
| （无） | `scripts.preuninstall` | 新增（可选） |
| （无） | `scripts.postuninstall` | 新增（可选） |
| （无） | `scripts.prepare` | 新增（可选） |

### 8.3 向后兼容策略

**双向兼容（推荐方案）：**
- 读取时：兼容新旧格式（如 `scripts.init` 自动映射为 `scripts.postinstall`）
- 写入时：使用新格式（`scripts.postinstall`）
- 现有 17 个 `*.plugin.yaml` 一次性迁移到新格式
- 已安装的旧插件文件不强制迁移（读取代码兼容）

### 8.4 跨 IDE 导出规则

导出时根据目标 IDE 拆分字段：

| 目标 IDE | 导出动作 |
|---|---|
| Claude Code | 生成 `.claude-plugin/plugin.json`（剔除 `llm/subagents/rules/envVars/scripts`，Claude 会忽略但 `--strict` 会警告），`.mcp.json`，`hooks/hooks.json`，`skills/`，`agents/`，`commands/` |
| Codex CLI | 生成 `.codex-plugin/plugin.json`（含 `interface`），`.mcp.json`，`hooks.json`，`skills/` |
| OpenCode | 仅导出 `skills/`、`mcp.json`、`agents/*.md` 到 `~/.config/opencode/` 对应目录，不走 plugin 机制 |
| Cursor / Trae / ZCode | 复用 Claude 格式或独立目录约定 |
| OpenClaw | 按 OpenClaw plugin slot 约定（如 `openclaw.json` 的 `plugins.slots`） |

## 9. 实施清单

- [x] 更新 `template/plugins/plugin.schema.yaml`（对齐标准字段 + 扩展字段）
- [ ] 更新 `scripts/lib/plugins.py` 的 `run_plugin_scripts`：支持 npm 生命周期 + 向后兼容 `init`
- [ ] 更新 `scripts/lib/plugins.py` 的 `uninstall_plugin`：执行 preuninstall/uninstall/postuninstall
- [ ] 更新 `frontend/src/stores/pluginBuild.ts`：读取兼容 `scripts.init`，写入新格式
- [ ] 迁移 17 个 `template/plugins/*.plugin.yaml`：补充 `license/keywords/homepage/repository/categories`
- [ ] 更新 `server/ai_generator/skills/plugin_generate.md`：AI 输出新格式
- [ ] 更新 `server/ai_generator/skills/plugin_design.md`：设计指南新字段说明

## 10. 参考链接

- Claude Code Plugins Reference: https://code.claude.com/docs/en/plugins-reference
- Codex CLI plugin-json-spec: https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md
- cc-marketplace PLUGIN_SCHEMA.md: https://github.com/ananddtyagi/cc-marketplace/blob/main/PLUGIN_SCHEMA.md
- claude-code-json-schema (非官方): https://github.com/hesreallyhim/claude-code-json-schema
- OpenCode Plugins: https://opencode.ai/docs/plugins/
- mem0 Codex 集成: https://docs.mem0.ai/integrations/codex
- npm scripts: https://docs.npmjs.com/cli/v10/using-npm/scripts
- VSCode Extension Manifest: https://code.visualstudio.com/api/references/extension-manifest
