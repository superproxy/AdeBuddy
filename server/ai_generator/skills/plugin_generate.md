# Skill: 插件生成输出规范

## 输出格式

生成完成后，输出一个 YAML 代码块，包含完整的 plugin.yaml 配置。
不要输出任何多余的解释文字，只输出 YAML 代码块。

## 规范对齐

输出必须符合 `template/plugins/plugin.schema.yaml` 定义的字段：
- **标准字段**（对齐 Claude Code / Codex CLI / VSCode）：`name` / `version` / `description` / `author` / `license` / `keywords` / `categories`
- **AdeBuddy 扩展字段**（多 IDE 同步能力）：`mcpServers` / `skills` / `llm` / `subagents` / `rules` / `commands` / `hooks` / `envVars` / `scripts`
- `scripts` 对齐 npm 生命周期：`preinstall` / `install` / `postinstall` / `preuninstall` / `uninstall` / `postuninstall` / `prepare`

## 示例

用户需求："一个 Java 后端开发智能体，精通 Spring Boot，需要数据库和 Redis"

输出：
```yaml
name: java-backend-agent
version: "1.0.0"
description: "Java 后端开发智能体，精通 Spring Boot / MyBatis / MySQL / Redis"
author: "AdeBuddy"
license: "MIT"
keywords: [java, spring-boot, backend, mysql, redis]
categories: [backend]

mcpServers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]

skills:
  - name: "backend-patterns"
    source: "backend-patterns"
    description: "后端开发最佳实践"

llm:
  - provider: "openai"
    protocol: "openai"
    base_url: "https://api.openai.com/v1"
    models:
      - id: "gpt-4o"
        name: "GPT-4o"

subagents:
  - "java-dev"
  - "dev"

rules:
  - "backend/clean-code.md"
  - "backend/api-design.md"

commands:
  - "commit"
  - "review"
  - "test"

hooks: false
```

## 字段生成规则

### 标准字段（必填）

1. `name` — 英文短名，kebab-case，如 `java-backend-agent`
2. `version` — 默认 `"1.0.0"`，严格 semver
3. `description` — 简洁中文说明（≤80 字符）
4. `author` — 默认 `"AdeBuddy"`，除非用户指定其他
5. `license` — 默认 `"MIT"`，除非用户指定其他
6. `keywords` — 3-7 个发现标签（英文，小写，连字符分隔）
7. `categories` — 1-2 个分类，必须从枚举中选：
   `coding` / `frontend` / `backend` / `fullstack` / `embedded` / `testing` / `security` / `devops` / `ai` / `office` / `browser` / `database` / `documentation` / `other`

### 可选标准字段（仅在用户明确提供时生成）

- `homepage` / `repository` / `icon` / `defaultEnabled` / `dependencies` / `userConfig` / `interface` / `apps`

### AdeBuddy 扩展字段

- `mcpServers` — 仅在用户需求涉及外部工具时生成
- `skills` — 优先使用本地技能名或 GitHub 简写（`owner/repo[@skill]`）
- `llm` — 仅在用户指定 LLM Provider 时生成
- `subagents` / `commands` / `rules` — 只引用已存在的名称
- `hooks` — 用户未提及时设为 `false`
- `scripts` — 仅在需要安装外部依赖时生成，使用 npm 生命周期字段：
  - `install`：主安装命令（如 `npm i -g xxx`）
  - `postinstall`：安装后初始化（替代旧 `init` 字段）
  - 不要无故添加 `preinstall` / `prepare` 等其他生命周期

## 注意事项

1. 不要过度配置 — 只声明与需求相关的资源
2. 如果用户没有提到 MCP，不要添加 `mcpServers`
3. 如果用户没有提到 hooks，设为 `false`
4. `keywords` 与 `categories` 应反映插件实际能力，避免堆砌
5. 输出必须是合法 YAML，字符串值建议加引号
