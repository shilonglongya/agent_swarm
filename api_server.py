"""
Agent Swarm API Server - DT_Project
多智能体协作框架 - 主从LLM架构
"""
import asyncio
import os
import json
import uuid
import time
import re
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检测是否运行在 PyInstaller 打包的可执行文件中
def get_base_path():
    """获取应用程序的基础路径"""
    if getattr(sys, 'frozen', False):
        # 运行在打包的可执行文件中
        return os.path.dirname(sys.executable)
    else:
        # 运行在普通 Python 脚本中
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# 配置文件路径
CONFIG_FILE = os.path.join(BASE_PATH, 'api_config.json')

app = Flask(__name__, static_folder=os.path.join(BASE_PATH, 'css'))
CORS(app)


# Serve static files
@app.route('/css/<path:filename>')
def serve_css(filename):
    css_path = os.path.join(BASE_PATH, 'css', filename)
    return send_file(css_path)


# ============ 日志系统 ============
class APILogger:
    """API 日志记录器"""

    def __init__(self):
        self.logs = []
        self.max_logs = 1000
        self.log_file = os.path.join(BASE_PATH, "app.log")

    def _write_to_file(self, message):
        """写入日志到文件"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def add(self, level, message, data=None):
        """添加日志"""
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]

        # 打印到控制台（带颜色）
        prefix = f"[{log_entry['time']}]"
        console_msg = ""
        if level == "INFO":
            console_msg = f"{prefix} [主LLM] {message}"
            print(console_msg)
        elif level == "SUCCESS":
            console_msg = f"{prefix} [✓] {message}"
            print(console_msg)
        elif level == "ERROR":
            console_msg = f"{prefix} [✗] {message}"
            print(console_msg)
        elif level == "SUB_AGENT":
            console_msg = f"{prefix} [子Agent] {message}"
            print(console_msg)
        else:
            console_msg = f"{prefix} [{level}] {message}"
            print(console_msg)

        if data:
            data_str = json.dumps(data, ensure_ascii=False)[:200]
            print(f"   Data: {data_str}...")
            self._write_to_file(f"{console_msg} | Data: {data_str}")
        else:
            self._write_to_file(console_msg)

    def info(self, message, data=None):
        self.add("INFO", message, data)

    def success(self, message, data=None):
        self.add("SUCCESS", message, data)

    def error(self, message, data=None):
        self.add("ERROR", message, data)

    def sub_agent(self, message, data=None):
        self.add("SUB_AGENT", message, data)

    def debug(self, message, data=None):
        self.add("DEBUG", message, data)

    def warning(self, message, data=None):
        self.add("WARNING", message, data)

    def get_all(self):
        return self.logs


logger = APILogger()


# ============ 配置保存系统 ============


def load_config():
    """加载保存的配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载配置失败: {e}")
    return {}


def save_config(config):
    """保存配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.success("配置已保存")
    except Exception as e:
        logger.error(f"保存配置失败: {e}")


# ============ 全局变量 ============
_llm_client = None
_config = None


# ============ 主LLM提示词 ============
MASTER_LLM_SYSTEM_PROMPT = """你是Agent Swarm主编排器，负责将复杂任务拆分为多个专业子Agent。

核心任务：
1. 分析任务需求
2. 设计多个专业子Agent协作完成
3. 为每个Agent编写详细提示词
4. 整合最终结果

【子Agent设计】
- 每个Agent必须有：id、name、description、role、goal、custom_prompt、output_format
- custom_prompt是Agent执行的完整提示词，必须包含：任务背景、具体任务、目标、要求
- output_format选择：markdown/对话/json/混合
- 至少设计5-20个Agent

【重要约束】
- 输出必须是合法JSON，不要有语法错误
- JSON字符串中不要使用大括号{}，用中文括号替代
- 直接输出JSON，不要其他文字说明"""

MASTER_LLM_DECOMPOSE_PROMPT = """分析以下任务，设计多个子Agent来协作完成。

任务：{task}

要求：
1. 分析任务需求
2. 设计5-20个子Agent，每个Agent有明确分工
3. 为每个Agent编写详细的执行提示词（custom_prompt字段）
4. 指定每个Agent的输出格式（output_format）

重要提示：
- custom_prompt必须包含：任务背景、具体任务、目标、要求
- 输出必须是合法的JSON，不要有语法错误
- 不要在JSON字符串中使用未转义的大括号{}
- 直接输出JSON，不要其他文字

JSON格式：
{
    "analysis": "任务分析",
    "subtask_count": 数量,
    "subtasks": [
        {
            "id": "task-1",
            "name": "Agent名称",
            "description": "任务描述",
            "role": "角色",
            "goal": "目标",
            "custom_prompt": "完整提示词（必须包含任务背景、具体内容、目标、要求）",
            "output_format": "markdown/对话/json/混合",
            "priority": "high/medium/low",
            "dependencies": []
        }
    ],
    "execution_plan": "执行计划",
    "final_strategy": "整合策略",
    "final_format": "最终输出格式"
}

请直接输出JSON："""

# 子Agent提示词模板
SUB_AGENT_PROMPTS = {
    "researcher": """你是一个专业的研究员（Researcher）。你的任务是从多角度收集和分析信息。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 进行全面的信息收集和分析
2. 分析多个来源的信息
3. 识别关键信息和趋势
4. 提供有据可查的分析结果

请直接开始执行任务，输出你的研究成果。""",

    "analyst": """你是一个专业的数据分析师（Analyst）。你的任务是处理信息并提炼洞见。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 分析数据/信息的模式和结构
2. 识别关键趋势和异常
3. 提供深入的洞察和建议
4. 使用清晰的数据支撑你的结论

请直接开始分析，输出你的分析结果。""",

    "writer": """你是一个专业的内容创作者（Writer）。你的任务是创建高质量的内容。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 创建清晰、准确、有吸引力的内容
2. 根据目标受众调整风格
3. 确保内容的逻辑连贯性
4. 提供有价值的观点和信息

请直接开始创作，输出你的内容。""",

    "coder": """你是一个专业的程序员（Coder）。你的任务是实现技术方案。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 提供清晰、可维护的代码
2. 添加适当的注释和文档
3. 考虑边界情况和错误处理
4. 解释你的实现思路

请直接开始编码，输出你的代码和说明。""",

    "reviewer": """你是一个专业的质量审查员（Reviewer）。你的任务是验证和审查工作质量。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 全面检查工作的完整性和准确性
2. 识别潜在的问题和错误
3. 提供具体的改进建议
4. 评估工作是否满足要求

请直接开始审查，输出你的审查报告。""",

    "planner": """你是一个专业的规划师（Planner）。你的任务是制定详细的执行计划。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 分析任务需求和约束条件
2. 制定清晰、可执行的计划
3. 考虑资源分配和时间安排
4. 识别潜在风险和应对措施

请直接开始规划，输出你的计划。""",

    "coordinator": """你是一个专业的协调员（Coordinator）。你的任务是协调多方资源和进度。

【任务】
{subtask_description}

【目标】
{goal}

【要求】
1. 协调各方资源和进度
2. 解决冲突和问题
3. 确保信息畅通
4. 推动任务按计划进行

请直接开始协调，输出你的协调结果。"""
}

# 结果整合提示词
AGGREGATION_PROMPT = """你是结果整合专家。请将多个子Agent的工作成果整合为最终输出。

【原始任务】
{task}

【各子任务执行结果】
{results}

【整合策略】
{strategy}

【最终输出格式要求】
{final_format}

请按照上述格式要求输出最终结果，整合所有有价值的内容。
确保内容的连贯性、完整性和专业性。

最终输出："""


# ============ 辅助函数 ============
def get_role_icon(role):
    """获取角色图标"""
    icons = {
        "researcher": "R",
        "analyst": "A",
        "writer": "W",
        "coder": "C",
        "reviewer": "V",
        "planner": "P",
        "coordinator": "O",
        "default": "G"
    }
    return icons.get(role, icons["default"])


def parse_json_response(response_text):
    """解析JSON响应，增强健壮性"""
    if not response_text:
        return None
    
    # 清理响应文本
    cleaned_text = response_text.strip()
    
    # 1. 尝试提取JSON部分（支持多层嵌套）
    # 查找第一个 { 到最后一个 }
    start_idx = cleaned_text.find('{')
    end_idx = cleaned_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = cleaned_text[start_idx:end_idx+1]
        try:
            result = json.loads(json_str)
            # 验证是否包含必要的字段
            if isinstance(result, dict) and 'subtasks' in result:
                return result
        except json.JSONDecodeError as e:
            pass
    
    # 2. 尝试修复常见的JSON问题
    # 移除可能的markdown代码块标记
    cleaned = cleaned_text
    if cleaned.startswith('```'):
        # 移除开头的 ```json 或 ``` 等
        lines = cleaned.split('\n')
        if lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        cleaned = '\n'.join(lines).strip()
    
    # 3. 再次尝试解析
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict) and 'subtasks' in result:
            return result
    except:
        pass
    
    # 4. 使用正则提取关键字段，尝试手动构建
    try:
        # 提取subtask_count
        count_match = re.search(r'"subtask_count"\s*:\s*(\d+)', cleaned_text)
        subtask_count = int(count_match.group(1)) if count_match else 0
        
        # 提取analysis
        analysis_match = re.search(r'"analysis"\s*:\s*"([^"]*)"', cleaned_text)
        analysis = analysis_match.group(1) if analysis_match else ""
        
        # 提取subtasks数组（简化处理）
        subtasks = []
        # 尝试找到subtasks部分
        subtasks_start = cleaned_text.find('"subtasks"')
        if subtasks_start != -1:
            # 简单处理：如果找不到完整的subtasks，至少尝试返回基本结构
            pass
        
        # 如果能提取到基本结构，就返回
        if subtask_count > 0:
            return {
                "analysis": analysis,
                "subtask_count": subtask_count,
                "subtasks": [],
                "execution_plan": "执行计划",
                "final_strategy": "整合策略"
            }
    except:
        pass
    
    # 5. 最后尝试：查找任何类似JSON的对象
    for pattern in [r'\{[^{}]*\}', r'\[[^\[\]]*\]']:
        matches = re.findall(pattern, cleaned_text)
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, dict) and 'subtasks' in result:
                    return result
            except:
                continue
    
    return None


def get_format_guidance(output_format):
    """根据输出格式返回格式指导"""
    format_lower = output_format.lower().strip()
    
    if "markdown" in format_lower:
        return """请使用Markdown格式输出，包含：
- 清晰的标题层次（# ## ###）
- 有序或无序列表
- 代码块（使用```包裹）
- 适当的加粗、斜体
- 如有数据，使用表格呈现
保持逻辑清晰，结构严谨。"""
    
    elif "json" in format_lower:
        return """请直接输出JSON格式，不要包含任何其他文字说明。
JSON应该包含所有必要的数据字段。"""
    
    elif "对话" in format_lower or "chat" in format_lower:
        return """请用自然的口语化方式回答，就像在与人对话一样。
不需要严格的结构，可以有适当的语气词和转折。
保持友好、亲切的表达风格。"""
    
    elif "混合" in format_lower or "mix" in format_lower:
        return """根据内容选择最合适的表达方式：
- 逻辑性强的内容使用Markdown结构
- 解释性内容使用口语化表达
- 数据内容使用表格或代码块
灵活运用各种格式，让输出清晰易读。"""
    
    else:
        # 默认使用对话格式
        return """请用自然、清晰的方式回答。
根据内容需要，可以适当使用格式来增强可读性。"""


# ============ API路由 ============
@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file(os.path.join(BASE_PATH, 'index.html'))


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "message": "Agent Swarm API (DT_Project) is running",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取所有日志"""
    return jsonify({
        "success": True,
        "logs": logger.get_all()
    })


@app.route('/api/models', methods=['POST'])
def list_models():
    """获取模型列表"""
    data = request.json
    api_key = data.get('apiKey', '')
    base_url = data.get('baseUrl', '')

    if not api_key:
        return jsonify({"error": "API Key is required"}), 400

    try:
        logger.info("正在获取模型列表...", {"base_url": base_url or "OpenAI"})

        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None,
            timeout=30
        )

        # 获取模型列表
        models = client.models.list()

        # 过滤和排序模型
        model_list = []
        for m in models.data:
            model_list.append({
                "id": m.id,
                "created": m.created,
                "object": m.object
            })

        # 按创建时间排序（最新的在前）
        model_list.sort(key=lambda x: x.get('created', 0), reverse=True)

        logger.success(f"获取到 {len(model_list)} 个模型")

        return jsonify({
            "success": True,
            "models": model_list
        })

    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/saved-config', methods=['GET'])
def get_saved_config():
    """获取保存的配置"""
    config = load_config()
    has_key = bool(config.get('apiKey'))

    # 不返回实际的 API Key
    safe_config = {
        "baseUrl": config.get('baseUrl', ''),
        "model": config.get('model', ''),
        "hasKey": has_key
    }

    return jsonify({
        "saved": has_key,
        "config": safe_config
    })


@app.route('/api/config', methods=['POST'])
def configure():
    """配置 API"""
    global _llm_client, _config

    data = request.json
    api_key = data.get('apiKey', '')
    base_url = data.get('baseUrl', '')
    model = data.get('model', 'gpt-4')
    save_config_flag = data.get('saveConfig', False)

    if not api_key:
        return jsonify({"error": "API Key is required"}), 400

    try:
        logger.info("正在配置 API...", {"model": model, "base_url": base_url or "OpenAI"})

        # 测试连接
        from openai import OpenAI
        _llm_client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None,
            timeout=120
        )

        response = _llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )

        logger.success(f"LLM 连接成功! 响应: {response.choices[0].message.content}")

        # 保存配置
        _config = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }

        if save_config_flag:
            save_config({
                "baseUrl": base_url,
                "model": model,
                "apiKey": api_key
            })

        return jsonify({
            "success": True,
            "message": f"已连接模型: {model}"
        })

    except Exception as e:
        import traceback
        logger.error(f"配置失败: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/execute/agent-swarm', methods=['POST'])
def execute_agent_swarm():
    """
    Agent Swarm 执行
    主LLM分析任务 -> 拆解 -> 子LLM执行 -> 汇总结果
    """
    global _llm_client, _config

    if not _llm_client:
        return jsonify({"error": "请先配置API"}), 400

    data = request.json
    task = data.get('task', '')

    if not task:
        return jsonify({"error": "任务不能为空"}), 400

    def generate():
        """生成流式响应"""
        task_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()

        try:
            # 发送任务开始消息
            yield "data: " + json.dumps({
                "type": "start",
                "task_id": task_id,
                "message": "开始执行任务"
            }, ensure_ascii=False) + "\n\n"

            logger.info(f"[{task_id}] 开始分析任务: {task}")

            # ===== 阶段1: 主LLM分析任务 =====
            logger.info(f"[{task_id}] ========== 主LLM分析任务 ==========")
            yield "data: " + json.dumps({
                "type": "stage",
                "stage": "master_analyze",
                "message": "主LLM正在分析任务..."
            }, ensure_ascii=False) + "\n\n"

            # 主LLM分析
            master_prompt = MASTER_LLM_DECOMPOSE_PROMPT.replace("{task}", task)
            master_response = _llm_client.chat.completions.create(
                model=_config["model"],
                messages=[
                    {"role": "system", "content": MASTER_LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": master_prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                stream=True
            )

            # 收集完整响应
            master_content = ""
            empty_chunk_count = 0
            try:
                for chunk in master_response:
                    # 检查chunk是否有效
                    if not chunk:
                        empty_chunk_count += 1
                        continue
                    if not hasattr(chunk, 'choices') or not chunk.choices:
                        empty_chunk_count += 1
                        continue
                    if chunk.choices[0] is None:
                        empty_chunk_count += 1
                        continue
                    # 检查delta是否存在且有内容
                    delta = chunk.choices[0].delta
                    if not delta:
                        empty_chunk_count += 1
                        continue
                    content = delta.content
                    if content:
                        master_content += content
                        yield "data: " + json.dumps({
                            "type": "master_thinking",
                            "chunk": content
                        }, ensure_ascii=False) + "\n\n"
                    else:
                        empty_chunk_count += 1

                # 如果收集到的内容为空，尝试使用非流式API
                if not master_content and empty_chunk_count > 0:
                    logger.warning(f"[{task_id}] 流式响应内容为空({empty_chunk_count}个空chunk)，尝试非流式API...")
                    try:
                        sync_prompt = MASTER_LLM_DECOMPOSE_PROMPT.replace("{task}", task)
                        sync_response = _llm_client.chat.completions.create(
                            model=_config["model"],
                            messages=[
                                {"role": "system", "content": MASTER_LLM_SYSTEM_PROMPT},
                                {"role": "user", "content": sync_prompt}
                            ],
                            temperature=0.7,
                            max_tokens=4000,
                            stream=False
                        )
                        if sync_response.choices and sync_response.choices[0].message.content:
                            master_content = sync_response.choices[0].message.content
                            logger.success(f"[{task_id}] 非流式API获取到内容，长度: {len(master_content)}")
                    except Exception as sync_err:
                        logger.error(f"[{task_id}] 非流式API也失败: {sync_err}")

            except Exception as e:
                logger.error(f"[{task_id}] 主LLM响应解析失败: {e}")
                master_content = ""

            logger.success(f"[{task_id}] 主LLM分析完成，内容长度: {len(master_content)}")

            # 解析主LLM的响应
            decomposition = parse_json_response(master_content)

            if not decomposition or "subtasks" not in decomposition:
                # 如果解析失败，创建默认分解
                decomposition = {
                    "analysis": master_content[:500],
                    "subtask_count": 3,
                    "subtasks": [
                        {"id": "task-1", "name": "分析任务", "description": "分析任务需求", "role": "analyst", "goal": "理解任务需求"},
                        {"id": "task-2", "name": "执行任务", "description": "执行核心任务", "role": "writer", "goal": "完成任务"},
                        {"id": "task-3", "name": "审查结果", "description": "审查和完善结果", "role": "reviewer", "goal": "确保质量"}
                    ]
                }

            subtasks = decomposition.get("subtasks", [])
            logger.success(f"[{task_id}] 任务分解完成: {len(subtasks)} 个子任务")

            # 发送分解结果
            yield "data: " + json.dumps({
                "type": "decomposition",
                "analysis": decomposition.get("analysis", ""),
                "subtasks": subtasks,
                "subtask_count": len(subtasks),
                "execution_plan": decomposition.get("execution_plan", "")
            }, ensure_ascii=False) + "\n\n"

            # ===== 阶段2: 子Agent并行执行 =====
            logger.info(f"[{task_id}] ========== 子Agent并行执行 ==========")
            yield "data: " + json.dumps({
                "type": "stage",
                "stage": "sub_agents_execute",
                "message": f"正在调度 {len(subtasks)} 个子Agent..."
            }, ensure_ascii=False) + "\n\n"

            # 为每个子任务创建执行流
            subtask_results = []

            for i, subtask in enumerate(subtasks):
                role = subtask.get("role", "writer")
                subtask_id = subtask.get("id", f"task-{i+1}")
                subtask_name = subtask.get("name", f"子任务{i+1}")
                subtask_desc = subtask.get("description", "")
                goal = subtask.get("goal", "")

                role_icon = get_role_icon(role)
                logger.sub_agent(f"[{role_icon}] {subtask_name} 开始执行 | role={role}")
                logger.info(f"[{subtask_id}] 任务描述: {subtask_desc[:100]}...")
                logger.info(f"[{subtask_id}] 目标: {goal}")

                # 检查LLM客户端状态
                logger.info(f"[{subtask_id}] 检查LLM客户端: _llm_client={bool(_llm_client)}, _config={bool(_config)}")
                if not _llm_client:
                    logger.error(f"[{subtask_id}] LLM客户端未初始化!")
                    yield "data: " + json.dumps({
                        "type": "subtask_error",
                        "subtask_id": subtask_id,
                        "error": "LLM客户端未初始化"
                    }, ensure_ascii=False) + "\n\n"
                    continue

                if "model" not in _config:
                    logger.error(f"[{subtask_id}] 模型未配置! _config.keys={list(_config.keys())}")
                    yield "data: " + json.dumps({
                        "type": "subtask_error",
                        "subtask_id": subtask_id,
                        "error": "模型未配置"
                    }, ensure_ascii=False) + "\n\n"
                    continue

                logger.info(f"[{subtask_id}] LLM客户端正常，模型: {_config['model']}")

                # 发送子任务开始
                yield "data: " + json.dumps({
                    "type": "subtask_start",
                    "subtask_id": subtask_id,
                    "subtask_name": subtask_name,
                    "role": role,
                    "role_icon": role_icon,
                    "message": f"[{role_icon}] {subtask_name} 开始执行..."
                }, ensure_ascii=False) + "\n\n"

                # 获取子Agent提示词
                logger.info(f"[{subtask_id}] 检查提示词模板: role={role}")

                # 修复: 先将大括号替换为全角括号，避免与format冲突
                safe_subtask_desc = subtask_desc.replace("{", "【").replace("}", "】")
                safe_goal = goal.replace("{", "【").replace("}", "】")
                
                # 优先使用自定义提示词（custom_prompt），如果没有则使用模板
                custom_prompt = subtask.get("custom_prompt", "")
                # 获取输出格式定制
                output_format = subtask.get("output_format", "对话")

                # 调试日志：显示获取到的字段
                logger.info(f"[{subtask_id}] 获取到字段: description长度={len(subtask_desc)}, goal长度={len(goal)}, custom_prompt长度={len(custom_prompt)}, output_format={output_format}")

                try:
                    if custom_prompt:
                        # 使用主Agent为这个子任务专门编写的提示词
                        logger.info(f"[{subtask_id}] 使用自定义提示词，输出格式: {output_format}")
                        logger.info(f"[{subtask_id}] custom_prompt前100字: {custom_prompt[:100]}...")
                        # 清理custom_prompt中的大括号
                        sub_prompt = custom_prompt.replace("{", "【").replace("}", "】")
                        # 在提示词末尾强调输出格式要求
                        format_guidance = get_format_guidance(output_format)
                        sub_prompt += f"\n\n【输出格式要求】\n{format_guidance}"
                    else:
                        # 使用默认模板，但融合description和goal
                        logger.info(f"[{subtask_id}] 准备格式化 {role} 提示词...")
                        # 构建包含description和goal的提示词
                        base_prompt = SUB_AGENT_PROMPTS.get(role, SUB_AGENT_PROMPTS["writer"])
                        sub_prompt = base_prompt.replace("{subtask_description}", safe_subtask_desc).replace("{goal}", safe_goal)
                        # 如果description或goal有内容，追加到提示词中
                        if safe_subtask_desc or safe_goal:
                            sub_prompt += f"\n\n【任务详情】\n描述: {safe_subtask_desc}\n目标: {safe_goal}"
                        logger.info(f"[{subtask_id}] 使用 {role} 提示词模板")
                except Exception as e:
                    logger.error(f"[{subtask_id}] 提示词格式化失败: {e}")
                    yield "data: " + json.dumps({
                        "type": "subtask_error",
                        "subtask_id": subtask_id,
                        "error": f"提示词格式化失败: {str(e)}"
                    }, ensure_ascii=False) + "\n\n"
                    continue

                # 执行子任务（流式输出）
                logger.info(f"[{subtask_id}] 调用LLM执行子任务...")
                logger.info(f"[{subtask_id}] model={_config.get('model')} 已配置LLM={bool(_llm_client)}")
                try:
                    # 调用LLM执行子任务
                    logger.info(f"[{subtask_id}] 准备调用OpenAI API...")
                    
                    # 根据是否有自定义提示词来决定system prompt
                    if custom_prompt:
                        system_prompt = f"你是一个专业的{subtask_name}。请直接回答问题，不要重复角色设定。"
                    else:
                        system_prompt = f"你是一个专业的{role}。请直接回答问题，不要重复角色设定。"
                    
                    sub_response = _llm_client.chat.completions.create(
                        model=_config["model"],
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": sub_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000,
                        stream=True
                    )
                    logger.info(f"[{subtask_id}] API调用成功，开始接收流式响应")

                    sub_output = ""
                    empty_chunk_count = 0
                    try:
                        for chunk in sub_response:
                            if not chunk:
                                empty_chunk_count += 1
                                continue
                            if not hasattr(chunk, 'choices') or not chunk.choices:
                                empty_chunk_count += 1
                                continue
                            if chunk.choices[0] is None:
                                empty_chunk_count += 1
                                continue
                            delta = chunk.choices[0].delta
                            if not delta:
                                empty_chunk_count += 1
                                continue
                            content = delta.content
                            if content:
                                sub_output += content
                                yield "data: " + json.dumps({
                                    "type": "subtask_stream",
                                    "subtask_id": subtask_id,
                                    "subtask_name": subtask_name,
                                    "role": role,
                                    "role_icon": role_icon,
                                    "chunk": content
                                }, ensure_ascii=False) + "\n\n"
                            else:
                                empty_chunk_count += 1

                        # 如果内容为空，尝试非流式API
                        if not sub_output and empty_chunk_count > 0:
                            logger.warning(f"[{subtask_id}] 流式响应为空，尝试非流式...")
                            try:
                                sync_response = _llm_client.chat.completions.create(
                                    model=_config["model"],
                                    messages=[
                                        {"role": "system", "content": f"你是一个专业的{role}。请直接回答问题，不要重复角色设定。"},
                                        {"role": "user", "content": sub_prompt}
                                    ],
                                    temperature=0.7,
                                    max_tokens=4000,
                                    stream=False
                                )
                                if sync_response.choices and sync_response.choices[0].message.content:
                                    sub_output = sync_response.choices[0].message.content
                                    logger.success(f"[{subtask_id}] 非流式获取内容: {len(sub_output)}")
                            except Exception as sync_err:
                                logger.error(f"[{subtask_id}] 非流式也失败: {sync_err}")

                    except Exception as e:
                        logger.error(f"[{subtask_id}] 子LLM响应解析失败: {e}")

                    subtask_results.append({
                        "id": subtask_id,
                        "name": subtask_name,
                        "role": role,
                        "output": sub_output,
                        "status": "completed"
                    })

                    logger.sub_agent(f"[{role_icon}] {subtask_name} 执行完成")

                    # 发送子任务完成
                    yield "data: " + json.dumps({
                        "type": "subtask_done",
                        "subtask_id": subtask_id,
                        "subtask_name": subtask_name,
                        "role": role,
                        "role_icon": role_icon,
                        "output": sub_output,
                        "status": "completed"
                    }, ensure_ascii=False) + "\n\n"

                except Exception as e:
                    logger.error(f"子任务执行失败: {str(e)}")
                    subtask_results.append({
                        "id": subtask_id,
                        "name": subtask_name,
                        "role": role,
                        "output": f"执行失败: {str(e)}",
                        "status": "failed"
                    })

                    yield "data: " + json.dumps({
                        "type": "subtask_error",
                        "subtask_id": subtask_id,
                        "error": str(e)
                    }, ensure_ascii=False) + "\n\n"

            # ===== 阶段3: 结果汇总 =====
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{task_id}] ========== 结果汇总 ==========")
            yield "data: " + json.dumps({
                "type": "stage",
                "stage": "aggregation",
                "message": "正在整合结果..."
            }, ensure_ascii=False) + "\n\n"

            # 构建汇总内容
            results_text = "\n\n".join([
                f"【{r['name']}】（{r['role']}）\n{r['output']}"
                for r in subtask_results
            ])

            # 主LLM汇总
            try:
                # 获取最终输出格式要求，如果没有则使用默认
                final_format = decomposition.get("final_format", "使用清晰的Markdown格式，包含适当的标题、列表和结构")
                aggregation_prompt = AGGREGATION_PROMPT.replace("{task}", task).replace("{results}", results_text).replace("{strategy}", decomposition.get("final_strategy", "综合所有观点，形成最终输出")).replace("{final_format}", final_format)
                final_response = _llm_client.chat.completions.create(
                    model=_config["model"],
                    messages=[
                        {"role": "system", "content": "你是一个专业的总结专家。请将多个部分的输出整合为一个连贯、完整的最终结果。"},
                        {"role": "user", "content": aggregation_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=4000,
                    stream=True
                )

                final_output = ""
                try:
                    for chunk in final_response:
                        if not chunk.choices:
                            continue
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            final_output += content
                            yield "data: " + json.dumps({
                                "type": "final_stream",
                                "chunk": content
                            }, ensure_ascii=False) + "\n\n"
                except Exception as e:
                    logger.error(f"[{task_id}] 结果汇总解析失败: {e}")

                logger.success(f"[{task_id}] ========== 执行完成 ==========")
                logger.success(f"[{task_id}] 耗时: {elapsed:.2f}s, 子任务: {len(subtasks)}")

                # 发送最终完成
                yield "data: " + json.dumps({
                    "type": "done",
                    "task_id": task_id,
                    "time": elapsed,
                    "subtask_count": len(subtasks),
                    "final_output": final_output
                }, ensure_ascii=False) + "\n\n"

            except Exception as e:
                logger.error(f"汇总失败: {str(e)}")
                yield "data: " + json.dumps({
                    "type": "aggregation_error",
                    "message": str(e),
                    "partial_results": subtask_results
                }, ensure_ascii=False) + "\n\n"

                logger.success(f"[{task_id}] ========== 执行完成(部分) ==========")
                yield "data: " + json.dumps({
                    "type": "done",
                    "task_id": task_id,
                    "time": elapsed,
                    "subtask_count": len(subtasks),
                    "final_output": results_text,
                    "partial": True
                }, ensure_ascii=False) + "\n\n"

        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"[{task_id}] 执行失败: {error_msg}")
            traceback.print_exc()

            yield "data: " + json.dumps({
                "type": "error",
                "message": error_msg
            }, ensure_ascii=False) + "\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/execute/simple', methods=['POST'])
def execute_simple():
    """简单执行模式 - 不使用Agent Swarm"""
    global _llm_client, _config

    if not _llm_client:
        return jsonify({"error": "请先配置API"}), 400

    data = request.json
    task = data.get('task', '')

    if not task:
        return jsonify({"error": "任务不能为空"}), 400

    def generate():
        task_id = str(uuid.uuid4())[:8]

        try:
            yield "data: " + json.dumps({
                "type": "start",
                "message": "开始执行..."
            }, ensure_ascii=False) + "\n\n"

            response = _llm_client.chat.completions.create(
                model=_config["model"],
                messages=[
                    {"role": "user", "content": task}
                ],
                temperature=0.7,
                max_tokens=4000,
                stream=True
            )

            full_output = ""
            for chunk in response:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_output += content
                    yield "data: " + json.dumps({
                        "type": "content",
                        "chunk": content
                    }, ensure_ascii=False) + "\n\n"

            yield "data: " + json.dumps({
                "type": "done",
                "output": full_output
            }, ensure_ascii=False) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "type": "error",
                "message": str(e)
            }, ensure_ascii=False) + "\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("=" * 60)
    print("   Agent Swarm API Server (DT_Project)")
    print("=" * 60)
    print(f"Server running at http://localhost:{port}")
    print(f"Open http://localhost:{port} in your browser")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
