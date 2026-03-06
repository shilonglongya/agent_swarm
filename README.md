# Agent Swarm Framework

![正宗老代码](e60294758e15ac0816aa9c7d8ef825fd.jpg)

一个功能强大的本地多智能体协作框架，支持动态任务分解、并行子代理执行和智能结果汇总。

## 特性

- **动态任务分解** - 主LLM智能分析任务，动态创建多个专业子Agent
- **自由Agent设计** - 主Agent可自由定义子Agent名称、角色和提示词
- **自定义输出格式** - 每个子Agent可定制输出格式（markdown/对话/json/混合）
- **并行执行引擎** - 支持多个子Agent并行工作
- **智能结果汇总** - 主Agent定制最终输出格式，整合所有子Agent结果
- **流式输出** - 支持实时流式响应，前端自动滚动
- **多LLM支持** - 支持 OpenAI、SiliconFlow、Anthropic 等 OpenAI 兼容 API

## 快速开始

### 1. 安装依赖

```bash
cd agent_swarm
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 方式1：直接运行
python api_server.py

# 方式2：使用启动脚本（Windows）
start_agent_swarm.bat
```

### 3. 访问Web界面

打开浏览器访问：`http://localhost:5000`

### 4. 配置API

在Web界面中：
1. 输入 API Key
2. 选择或输入模型名称
3. 点击"连接 API"

## 使用方法

### 基础用法

1. 在Web界面输入任务
2. 选择"Agent集群"模式
3. 点击"执行任务"
4. 观察子Agent并行执行过程
5. 获取最终整合结果

### 子Agent设计示例

主Agent会自动将任务分解为多个专业子Agent，每个子Agent：

- **自定义名称** - 如"市场调研专家"、"竞品分析师"等
- **自定义提示词** - 主Agent为每个子Agent编写专门的任务提示词
- **自定义输出格式** - 根据任务性质选择合适的输出格式
  - `markdown` - 技术文档、代码分析、报告（结构化输出）
  - `对话` - 头脑风暴、讨论（口语化表达）
  - `json` - 结构化数据
  - `混合` - 灵活组合

### 输出格式定制

- **子Agent级别** - 每个子Agent可选择不同的输出格式
- **最终输出** - 主Agent定制最终整合结果的格式

## 架构

```
Agent Swarm Architecture
┌─────────────────────────────────────────────────────┐
│                 主LLM (Master)                        │
│         - 任务分析                                    │
│         - 动态创建子Agent                             │
│         - 定制提示词和输出格式                         │
│         - 结果整合                                    │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐   ┌───▼────┐   ┌────▼────┐
    │ 子Agent │   │子Agent │   │ 子Agent │
    │   1     │   │   2    │   │   N    │
    │(自定义角色)│   │(自定义角色)│   │(自定义角色)│
    │自定义格式 │   │自定义格式 │   │自定义格式 │
    └─────────┘   └────────┘   └─────────┘
```

## 子Agent角色

主Agent可以自由创建以下类型的子Agent（仅作参考，可自由扩展）：

- **researcher** - 研究专家
- **analyst** - 数据分析师
- **writer** - 内容创作者
- **coder** - 软件开发者
- **reviewer** - 质量审查员
- **planner** - 规划师
- **coordinator** - 协调员
- **editor** - 编辑
- **expert** - 领域专家
- **consultant** - 顾问
- **自定义角色** - 主Agent可自由创造新角色

## API 接口

### 配置API

```bash
POST /api/config
{
  "apiKey": "your-api-key",
  "baseUrl": "https://api.siliconflow.com/v1",  # 可选
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

## 配置说明

### 支持的模型

- OpenAI: `gpt-4`, `gpt-3.5-turbo`
- SiliconFlow: `Qwen/Qwen2.5-72B-Instruct`, `deepseek-ai/DeepSeek-V2-Chat` 等
- 其他 OpenAI 兼容 API

### 环境变量

```env
# 可选：使用环境变量配置
OPENAI_API_KEY=your-key
PORT=5000
```

## 示例输出

执行任务后，你将看到：

1. **主LLM分析** - 主Agent分析任务，设计子Agent
2. **任务分解** - 显示创建的子Agent数量和角色
3. **子Agent执行** - 各子Agent并行执行任务
4. **流式输出** - 每个子Agent的输出实时显示
5. **最终整合** - 主Agent按定制格式整合结果

## 性能优化

1. **并行度** - 主Agent会根据任务复杂度自动决定子Agent数量
2. **超时设置** - 合理设置 API 超时时间
3. **流式输出** - 使用流式输出减少等待时间

## 技术栈

- **后端**: Python Flask
- **前端**: HTML/CSS/JavaScript
- **LLM**: OpenAI 兼容 API

## 许可证

MIT License
