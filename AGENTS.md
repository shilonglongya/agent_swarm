# Agent Swarm Framework 项目指南

## 项目概述

**Agent Swarm Framework (DT_Project)** 是一个功能强大的本地多智能体协作框架，支持动态任务分解、并行子代理执行和智能结果汇总。

### 核心特性

- **动态任务分解** - 主LLM智能分析任务，动态创建多个专业子Agent
- **自由Agent设计** - 主Agent可自由定义子Agent名称、角色和提示词
- **自定义输出格式** - 每个子Agent可定制输出格式（markdown/对话/json/混合）
- **并行执行引擎** - 支持多个子Agent并行工作
- **智能结果汇总** - 主Agent定制最终输出格式，整合所有子Agent结果
- **流式输出** - 支持实时流式响应，前端自动滚动
- **多LLM支持** - 支持 OpenAI、SiliconFlow、Anthropic 等 OpenAI 兼容 API

---

## 项目结构

```
agent_swarm/
├── main.py                 # 主入口文件 (CLI 模式)
├── api_server.py          # Flask API 服务器 (Web 模式)
├── index.html              # Web 前端页面
├── config/
│   └── settings.py         # 配置管理
├── llm/
│   └── client.py           # LLM 客户端封装
├── core/
│   ├── orchestrator.py    # 主编排器 (核心协调器)
│   ├── sub_agent.py       # 子代理系统
│   ├── task_decomposer.py # 任务分解器
│   ├── result_aggregator.py # 结果汇总器
│   └── parallel_executor.py # 并行执行器
├── css/                    # 前端样式
│   ├── base/              # 基础样式
│   ├── components/        # 组件样式
│   ├── layouts/           # 布局样式
│   └── animations/        # 动画样式
├── js/                     # 前端脚本
│   └── main.js            # 前端主逻辑
├── examples/               # 示例代码
│   ├── research_example.py
│   ├── content_creation_example.py
│   └── code_review_example.py
└── templates/              # 模板文件
```

---

## 启动方式

### 方式一：Web 界面模式（推荐）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python api_server.py

# 或使用启动脚本（Windows）
start_agent_swarm.bat
```

访问地址：`http://localhost:5000`

### 方式二：CLI 交互模式

```bash
# 设置环境变量
set OPENAI_API_KEY=your-api-key

# 运行示例
python main.py

# 或进入交互模式
python main.py --mode interactive
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `OPENAI_BASE_URL` | API 基础 URL | OpenAI 官方 |
| `LLM_PROVIDER` | LLM 提供商 | openai |
| `LLM_MODEL` | 模型名称 | gpt-4 |
| `LLM_TEMPERATURE` | 温度参数 | 0.7 |
| `MAX_SUB_AGENTS` | 最大子代理数 | 100 |
| `MAX_PARALLEL_TASKS` | 最大并行任务数 | 20 |

### 支持的模型

- **OpenAI**: `gpt-4`, `gpt-3.5-turbo`
- **SiliconFlow**: `Qwen/Qwen2.5-72B-Instruct`, `deepseek-ai/DeepSeek-V2-Chat` 等
- **其他 OpenAI 兼容 API**

---

## 核心架构

### 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                    主LLM (Master)                        │
│         - 任务分析                                       │
│         - 动态创建子Agent                                │
│         - 定制提示词和输出格式                            │
│         - 结果整合                                       │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌─────▼────┐    ┌─────▼────┐
    │ 子Agent │    │ 子Agent  │    │ 子Agent  │
    │    1    │    │    2     │    │    N     │
    └─────────┘    └──────────┘    └──────────┘
```

### 核心模块说明

| 模块 | 文件 | 功能 |
|------|------|------|
| 编排器 | `core/orchestrator.py` | 协调整个执行流程，管理任务分解、执行、汇总 |
| 子代理 | `core/sub_agent.py` | 执行具体的子任务，管理代理池 |
| 任务分解 | `core/task_decomposer.py` | 将复杂任务分解为可并行的子任务 |
| 结果汇总 | `core/result_aggregator.py` | 整合多个子代理的结果 |
| 并行执行 | `core/parallel_executor.py` | 并行调度多个子代理 |
| LLM 客户端 | `llm/client.py` | 封装 OpenAI API 调用 |

---

## 子代理角色

框架预定义以下子代理角色（可扩展）：

| 角色 | 说明 |
|------|------|
| `researcher` | 研究专家 - 收集和分析信息 |
| `analyst` | 数据分析师 - 处理数据、识别模式 |
| `writer` | 内容创作者 - 创建高质量内容 |
| `coder` | 程序员 - 实现技术方案 |
| `reviewer` | 质量审查员 - 验证和审查工作 |
| `planner` | 规划师 - 制定执行计划 |
| `coordinator` | 协调员 - 协调资源和进度 |

---

## API 接口

### 配置 API

```bash
POST /api/config
{
  "apiKey": "your-api-key",
  "baseUrl": "https://api.siliconflow.com/v1",
  "model": "Qwen/Qwen2.5-72B-Instruct",
  "saveConfig": true
}
```

### 执行任务

```bash
POST /api/execute/agent-swarm
{
  "task": "你的任务描述"
}
```

响应为 Server-Sent Events (SSE) 流式输出。

### 健康检查

```bash
GET /api/health
```

---

## 开发指南

### 代码规范

- 使用 Python 类型注解
- 遵循 PEP 8 风格
- 异步函数使用 `async/await`
- 错误处理使用 try-except

### 关键类说明

#### `AgentSwarmOrchestrator` (core/orchestrator.py)

主编排器类，负责协调整个任务执行流程。

```python
# 初始化
orchestrator = AgentSwarmOrchestrator(
    llm_client=llm_client,
    config=config.swarm,
    name="DemoSwarm"
)

# 执行任务
result = await orchestrator.execute(
    task="任务描述",
    strategy=AggregationStrategy.SYNTHESIS,
    progress_callback=lambda msg: print(msg)
)
```

#### `LLMClient` (llm/client.py)

LLM 客户端封装，支持同步和异步调用。

```python
# 异步调用
response = await llm.complete(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)

# 流式响应
async for chunk in llm.stream(messages=[...]):
    print(chunk, end="")
```

#### `TaskDecomposer` (core/task_decomposer.py)

任务分解器，将复杂任务分解为并行子任务。

```python
decomposition = await decomposer.decompose(
    task="复杂任务",
    context={"key": "value"},
    max_subtasks=20
)
```

---

## 示例用法

### Python 代码调用

```python
import asyncio
from config.settings import Config
from llm.client import LLMClient
from core.orchestrator import AgentSwarmOrchestrator, AggregationStrategy

async def main():
    config = Config.from_env()
    llm = LLMClient(config.llm)
    orchestrator = AgentSwarmOrchestrator(llm, config.swarm)
    
    result = await orchestrator.execute(
        task="分析 Python 和 JavaScript 的优缺点",
        strategy=AggregationStrategy.SYNTHESIS
    )
    
    print(result.aggregated_result.final_output)

asyncio.run(main())
```

### Web 界面使用

1. 打开 `http://localhost:5000`
2. 输入 API Key 并选择模型
3. 点击"连接 API"
4. 输入任务描述
5. 点击"执行任务"
6. 观察子Agent并行执行过程
7. 获取最终整合结果

---

## 故障排查

### 常见问题

1. **API 连接失败**
   - 检查 API Key 是否正确
   - 检查网络连接
   - 确认 base_url 设置正确

2. **任务执行超时**
   - 增加 `execution_timeout` 配置
   - 检查 API 响应时间

3. **子代理执行失败**
   - 查看日志输出
   - 检查子代理提示词格式
   - 确认输出格式设置正确

### 日志查看

- 控制台输出（带颜色标识）
- `app.log` 文件
- Web 界面的日志面板

---

## 技术栈

- **后端**: Python Flask
- **前端**: HTML/CSS/JavaScript
- **LLM**: OpenAI 兼容 API
- **依赖**: openai, flask, flask-cors, pydantic, rich 等

---

## 许可证

MIT License
