# Skill: 插件生成输出规范

## 输出格式

生成完成后，输出一个 YAML 代码块，包含完整的 plugin.yaml 配置。
不要输出任何多余的解释文字，只输出 YAML 代码块。

## 示例

用户需求："一个 Java 后端开发智能体，精通 Spring Boot，需要数据库和 Redis"

输出：
```yaml
name: java-backend-agent
version: "1.0.0"
description: "Java 后端开发智能体，精通 Spring Boot / MyBatis / MySQL / Redis"
author: "AdeBuddy"

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

## 注意事项

1. name 必须是英文短名，用连字符分隔，如 `java-backend-agent`
2. version 默认 "1.0.0"
3. 只声明与需求相关的资源，不要过度配置
4. 如果用户没有提到 MCP，不要添加
5. 如果用户没有提到 hooks，设为 false
6. subagents/commands/rules 只引用已存在的名称
7. skills 的 source 优先使用本地技能名或 GitHub 简写
