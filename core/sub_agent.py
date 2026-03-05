"""
Sub-agent 子代理系统
"""
import uuid
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from llm.client import LLMClient
from core.task_decomposer import SubTask, TaskType


class AgentStatus(Enum):
    """代理状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentResult:
    """代理执行结果"""
    subtask_id: str
    agent_id: str
    status: AgentStatus
    output: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "subtask_id": self.subtask_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "token_usage": self.token_usage,
            "metadata": self.metadata
        }


class SubAgent:
    """
    子代理 - 执行具体的子任务
    """
    
    def __init__(
        self,
        agent_id: str,
        role: str,
        llm_client: LLMClient,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ):
        self.agent_id = agent_id
        self.role = role
        self.llm = llm_client
        self.system_prompt = system_prompt or self._get_default_system_prompt(role)
        self.tools = tools or []
        self.status = AgentStatus.IDLE
        self.execution_history: List[Dict] = []
    
    def _get_default_system_prompt(self, role: str) -> str:
        """获取默认系统提示"""
        prompts = {
            "researcher": """You are a Research Specialist agent.
Your task is to gather, analyze, and synthesize information accurately.
Be thorough, cite sources when possible, and provide structured output.""",
            
            "analyst": """You are a Data Analyst agent.
Your task is to process information, identify patterns, and derive insights.
Use analytical frameworks and provide quantitative assessments when applicable.""",
            
            "writer": """You are a Content Writer agent.
Your task is to create clear, engaging, and well-structured content.
Adapt your writing style to the audience and purpose.""",
            
            "coder": """You are a Software Developer agent.
Your task is to write clean, efficient, and well-documented code.
Follow best practices and include error handling.""",
            
            "reviewer": """You are a Quality Reviewer agent.
Your task is to verify accuracy, check for errors, and ensure high standards.
Be critical but constructive in your feedback.""",
            
            "custom": """You are a specialized agent.
Execute your assigned task with expertise and attention to detail.
Provide high-quality output that meets the requirements."""
        }
        return prompts.get(role, prompts["custom"])
    
    async def execute(
        self,
        subtask: SubTask,
        context: Optional[Dict] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> AgentResult:
        """
        执行子任务
        
        Args:
            subtask: 子任务定义
            context: 执行上下文
            callback: 进度回调函数
        
        Returns:
            AgentResult 执行结果
        """
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        try:
            # 构建消息
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # 添加上下文
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                messages.append({
                    "role": "system",
                    "content": f"Context:\n{context_str}"
                })
            
            # 添加任务描述
            task_prompt = f"""Task: {subtask.name}
Description: {subtask.description}
Task Type: {subtask.task_type.value}

Execute this task and provide your output."""
            
            messages.append({"role": "user", "content": task_prompt})
            
            if callback:
                callback(f"[Agent {self.agent_id}] Starting task: {subtask.name}")
            
            # 调用 LLM
            response = await self.llm.complete(
                messages=messages,
                temperature=0.7,
                tools=self.tools if self.tools else None
            )
            
            execution_time = time.time() - start_time
            
            # 记录历史
            self.execution_history.append({
                "subtask_id": subtask.id,
                "task_name": subtask.name,
                "status": "completed",
                "execution_time": execution_time,
                "token_usage": response.get("usage", {})
            })
            
            self.status = AgentStatus.COMPLETED
            
            if callback:
                callback(f"[Agent {self.agent_id}] Completed task: {subtask.name}")
            
            return AgentResult(
                subtask_id=subtask.id,
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output=response["content"],
                execution_time=execution_time,
                token_usage=response.get("usage", {}),
                metadata={
                    "role": self.role,
                    "task_type": subtask.task_type.value
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.status = AgentStatus.FAILED
            
            error_msg = str(e)
            if callback:
                callback(f"[Agent {self.agent_id}] Failed: {error_msg}")
            
            return AgentResult(
                subtask_id=subtask.id,
                agent_id=self.agent_id,
                status=AgentStatus.FAILED,
                output="",
                error=error_msg,
                execution_time=execution_time
            )
    
    async def execute_with_streaming(
        self,
        subtask: SubTask,
        context: Optional[Dict] = None
    ) -> AgentResult:
        """带流式输出的执行"""
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Task: {subtask.name}\nDescription: {subtask.description}"}
            ]
            
            output_parts = []
            async for chunk in self.llm.stream(messages=messages):
                output_parts.append(chunk)
                print(chunk, end="", flush=True)
            
            execution_time = time.time() - start_time
            self.status = AgentStatus.COMPLETED
            
            return AgentResult(
                subtask_id=subtask.id,
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output="".join(output_parts),
                execution_time=execution_time
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                subtask_id=subtask.id,
                agent_id=self.agent_id,
                status=AgentStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_status(self) -> AgentStatus:
        """获取当前状态"""
        return self.status
    
    def reset(self):
        """重置代理状态"""
        self.status = AgentStatus.IDLE
        # 保留历史记录但标记为已完成


class SubAgentPool:
    """子代理池 - 管理和复用子代理"""
    
    def __init__(self, llm_client: LLMClient, max_agents: int = 100):
        self.llm = llm_client
        self.max_agents = max_agents
        self.agents: Dict[str, SubAgent] = {}
        self.role_agents: Dict[str, List[str]] = {}  # role -> agent_ids
        self._lock = asyncio.Lock()
    
    async def get_or_create_agent(
        self,
        role: str,
        system_prompt: Optional[str] = None
    ) -> SubAgent:
        """获取或创建代理"""
        async with self._lock:
            # 检查是否有空闲的该角色代理
            if role in self.role_agents:
                for agent_id in self.role_agents[role]:
                    agent = self.agents.get(agent_id)
                    if agent and agent.status == AgentStatus.IDLE:
                        return agent
            
            # 创建新代理
            agent_id = f"{role}-{uuid.uuid4().hex[:8]}"
            agent = SubAgent(
                agent_id=agent_id,
                role=role,
                llm_client=self.llm,
                system_prompt=system_prompt
            )
            
            self.agents[agent_id] = agent
            
            if role not in self.role_agents:
                self.role_agents[role] = []
            self.role_agents[role].append(agent_id)
            
            return agent
    
    async def release_agent(self, agent_id: str):
        """释放代理回池"""
        async with self._lock:
            agent = self.agents.get(agent_id)
            if agent:
                agent.reset()
    
    def get_pool_stats(self) -> Dict:
        """获取池统计信息"""
        stats = {
            "total_agents": len(self.agents),
            "idle_agents": 0,
            "running_agents": 0,
            "failed_agents": 0,
            "role_distribution": {}
        }
        
        for agent in self.agents.values():
            if agent.status == AgentStatus.IDLE:
                stats["idle_agents"] += 1
            elif agent.status == AgentStatus.RUNNING:
                stats["running_agents"] += 1
            elif agent.status == AgentStatus.FAILED:
                stats["failed_agents"] += 1
        
        for role, agent_ids in self.role_agents.items():
            stats["role_distribution"][role] = len(agent_ids)
        
        return stats
