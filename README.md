# AI Cognitive Nexus (认知中枢)

一个专业的、可动态编组的 AI 团队协作与编排的MCP。允许您通过简单的指令创建、管理和指挥由多个 AI 智能体 (Agent) 组成的层级化团队，以解决复杂和多阶段的任务。

## ✨ 功能特性 (Features)

  - 🤖 **动态团队编组**: 实时创建、更新和删除 AI 团队，成员可以是独立的 AI 智能体，甚至是其他团队，实现无限的层级化协作。
  - 🧠 **上下文情景注入**: 通过**人物 (Persona)** 和 **产品知识库 (Product)** 系统，为 AI 团队执行任务提供精确的角色扮演指令和专业领域知识。
  - 🔗 **层级化团队依赖**: 系统自动处理复杂的团队依赖关系（如团队A是团队B的成员），通过拓扑排序确保正确的初始化顺序，并能检测和防止循环依赖。
  - 💾 **持久化会话状态**: 内置会话管理器，能够跟踪和记录多轮对话历史，让 AI 团队具备长期记忆，胜任连续性任务。
  - 🔌 **可插拔大模型**: 支持通过环境变量在不同的大语言模型提供商（如 DeepSeek, OpenAILike 服务等）之间无缝切换，灵活适应不同成本和性能需求。
  - 🛠️ **可扩展智能体工具**: 为每个 AI 智能体配置专属工具集（如 `ThinkingTools`, `ExaTools`），赋予其超越语言能力的专业技能。
  - 🤝 **原生 MCP 协议**: 基于 Model Context Protocol 构建，可无缝与任何支持MCP的AI助手（如 OpenAI Assistants, Coze, Dify, Chatwise 等）集成。

## 🚀 核心概念

`Cognitive Nexus` 的强大能力源于以下几个核心概念的组合与协同：

| 概念 | 英文 | 作用 |
| :--- | :--- | :--- |
| **人物** | `Persona` | 定义 AI 在任务中需要扮演的角色、性格和目标。 |
| **产品** | `Product` | 为任务注入特定的背景知识和专业资料库。 |
| **角色/智能体** | `Agent` | 最小的执行单元。拥有特定角色、技能和工具的独立AI。 |
| **团队** | `Team` | 由多个 **Agent** 或 **其他 Team** 组成的协作单位，用于完成更宏大的目标。 |

**工作流程**: 当一个任务开始时，您可以指定一个**团队 (Team)** 作为执行者，并为其配备特定的**人物 (Persona)** 和**产品 (Product)** 作为上下文，从而精确地指导团队完成任务。

## ⚙️ 安装与配置

### 1\. 环境要求

  - Python 3.10+
  - `pip` 或 `uv` 等 Python 包管理工具
  - 支持 MCP 的 AI 客户端（如 Coze, Dify, 或其他兼容的Agent）

### 2\. 安装依赖

```bash
# 1. 克隆项目
git clone https://github.com/SimonUTD/ai-cognitive-nexus-mcp.git
cd ai-cognitive-nexus-mcp

# 2. (推荐) 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # on Windows, use `.venv\Scripts\activate`

# 3. 安装依赖
pip install -r requirements.txt
```


### 3\. 配置 `.env` 文件

这是配置模型提供商和 API Key 的**首选方式**。

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，填入你的配置信息
# LLM_PROVIDER: 设置默认使用的模型服务商 ("deepseek" 或 "openailike")
LLM_PROVIDER="deepseek"

# --- OpenAILike 服务商配置 ---
# 如果使用类似 ZhipuAI, Moonshot, Groq 等 OpenAI 兼容接口，请配置以下三项
OpenAILike_API_KEY="your_api_key_here"
OpenAILike_BASE_URL="https://api.example.com/v1"
OpenAILike_MODEL_ID="glm-4" # 用于团队协调的模型
OpenAILike_AGENT_MODEL_ID="glm-4" # 用于单个Agent的模型

# EXA 搜索 配置
EXA_API_KEY="your_exa_key_here" # 用于 EXA 工具的 API Key

```

### 4\. 启动服务器

直接运行 `main.py` 即可通过标准输入输出 (stdio) 启动 MCP 服务器。

```bash
python main.py
```

您也可以在支持 MCP 的客户端（如 Chatwise）中配置此命令，实现自动拉起。

## 📖 API 参考 (MCP Tools)

`Cognitive Nexus` 向 AI 助手暴露了一系列工具，用于管理和运行 AI 团队。

### 会话管理

  - `start_session(initial_context: str)`: 创建一个新会话，用于跟踪后续的交互历史。

### 人物 (Persona) 管理

  - `create_persona(persona_key: str, data: dict)`: 创建一个新的人物角色。
  - `list_personas()`: 列出所有可用的人物。
  - `get_persona(persona_key: str)`: 获取指定人物的详细信息。
  - `update_persona(persona_key: str, data: dict)`: 更新一个已存在的人物。
  - `delete_persona(persona_key: str)`: 删除一个人物。

### 产品 (Product) 管理

  - `create_product(product_key: str, data: dict)`: 创建一个新产品及其知识库。
  - `list_products()`: 列出所有产品。
  - `get_product(product_key: str)`: 获取产品详情和知识库。
  - `update_product(product_key: str, data: dict)`: 更新产品信息。
  - `delete_product(product_key: str)`: 删除一个产品。

### 角色/智能体 (Agent) 管理

  - `create_agent(agent_key: str, data: dict)`: 创建一个独立的 AI 智能体。
  - `list_agents()`: 列出所有智能体。
  - `get_agent(agent_key: str)`: 获取智能体配置。
  - `update_agent(agent_key: str, data: dict)`: 更新智能体配置（将自动重载所有团队）。
  - `delete_agent(agent_key: str)`: 删除一个智能体。

### 团队 (Team) 管理

  - `create_team(team_key: str, data: dict)`: 创建一个新团队。
  - `list_teams()`: 列出所有团队及其状态（激活/配置错误）。
  - `get_team_config(team_key: str)`: 获取团队的原始配置。
  - `update_team(team_key: str, data: dict)`: 更新团队配置（将自动尝试重载）。
  - `delete_team(team_key: str)`: 删除一个团队。

### 核心执行单元

  - **`run_ai_team(team_name: str, prompt: str, session_id: str, persona_key: str, product_key: str)`**
    这是框架的核心功能，用于指挥一个团队执行任务。
      - `team_name` (**必需**): 要运行的团队的 Key。
      - `prompt` (**必需**): 本次任务的核心指令。
      - `session_id` (可选): 关联的会话ID，用于加载历史记录和保存结果。
      - `persona_key` (可选): 本次任务中 AI 需要扮演的人物角色的 Key。
      - `product_key` (可选): 本次任务关联的产品的 Key，用于加载特定知识库。

## `[+]` 常见问题 (FAQ)

### Q: 如何创建一个“产品经理 Agent”和一个“研发团队”，并让他们协作？

A: 非常简单，分三步：

1.  **创建 Agent**: 调用 `create_agent` 创建一个 `product_manager` Agent，再创建两个研发 `developer_a` 和 `developer_b` Agent。在 `description` 和 `instructions` 中详细描述他们的职责。
2.  **创建 Team**: 调用 `create_team` 创建一个 `dev_team`，其 `members` 列表为 `["developer_a", "developer_b"]`。
3.  **运行**: 调用 `run_ai_team`，让 `product_manager` Agent 直接执行任务，或者创建一个更上层的 `project_team`，让 `product_manager` 和 `dev_team` 作为其成员，然后运行 `project_team`。

### Q: 如果我创建了一个循环依赖的团队（如团队A包含B，团队B又包含A），会发生什么？

A: 系统会自动检测到。在您调用 `create_team` 或 `update_team` 时，如果新的配置引入了循环依赖，该操作会失败并返回错误信息，同时您的修改将被自动回滚，确保系统始终处于可用的状态。

### Q: 我如何切换使用的AI模型，比如从智谱的 GLM-4 切换到月之暗面的 Moonshot？

A: 只需修改 `.env` 文件：

1.  设置 `LLM_PROVIDER="openailike"`。
2.  设置 `OpenAILike_API_KEY` 为你的 Moonshot API Key。
3.  设置 `OpenAILike_BASE_URL` 为 Moonshot 的服务地址 (`https://api.moonshot.cn/v1`)。
4.  设置 `OpenAILike_MODEL_ID` 为你想用的模型ID (如 `moonshot-v1-8k`)。
5.  设置 `EXA_API_KEY` 为你的 EXA API Key。
6.  重启 MCP 服务器即可生效。