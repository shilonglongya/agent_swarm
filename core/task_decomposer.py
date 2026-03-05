"""
任务分解器 - 将复杂任务分解为并行子任务
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from llm.client import LLMClient
from config.settings import AgentSwarmConfig


class TaskType(Enum):
    """任务类型"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITING = "writing"
    CODING = "coding"
    REVIEW = "review"
    CUSTOM = "custom"


@dataclass
class SubTask:
    """子任务定义"""
    id: str
    name: str
    description: str
    task_type: TaskType
    dependencies: List[str] = field(default_factory=list)
    estimated_complexity: int = 5  # 1-10
    assigned_role: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "dependencies": self.dependencies,
            "estimated_complexity": self.estimated_complexity,
            "assigned_role": self.assigned_role,
            "context": self.context
        }


@dataclass
class TaskDecomposition:
    """任务分解结果"""
    original_task: str
    subtasks: List[SubTask]
    parallel_groups: List[List[str]]  # 可并行执行的子任务组
    reasoning: str


class TaskDecomposer:
    """任务分解器 - 智能任务分解"""
    
    def __init__(self, llm_client: LLMClient, config: AgentSwarmConfig):
        self.llm = llm_client
        self.config = config
    
    async def decompose(
        self,
        task: str,
        context: Optional[Dict] = None,
        max_subtasks: int = 20
    ) -> TaskDecomposition:
        """
        将任务分解为子任务
        
        Args:
            task: 原始任务描述
            context: 额外上下文
            max_subtasks: 最大子任务数
        
        Returns:
            TaskDecomposition 对象
        """
        system_prompt = """You are an expert task decomposition engine, part of the Agent Swarm system.
Your role is to analyze complex tasks and break them down into parallelizable subtasks.

Rules:
1. Identify tasks that can be executed in parallel
2. Minimize dependencies between subtasks
3. Assign appropriate agent roles to each subtask
4. Estimate complexity (1-10) for each subtask
5. Group subtasks by their dependencies for parallel execution

Available agent roles:
- researcher: Gathers and analyzes information
- analyst: Processes data and identifies patterns  
- writer: Creates content and documentation
- coder: Implements technical solutions
- reviewer: Validates quality and accuracy
- custom: Specialized task-specific role

Output must be valid JSON with this structure:
{
    "reasoning": "explanation of decomposition strategy",
    "subtasks": [
        {
            "id": "unique-id",
            "name": "task name",
            "description": "detailed description",
            "task_type": "research|analysis|writing|coding|review|custom",
            "dependencies": ["id-of-dependency"],
            "estimated_complexity": 5,
            "assigned_role": "researcher|analyst|writer|coder|reviewer|custom"
        }
    ],
    "parallel_groups": [
        ["task-id-1", "task-id-2"],
        ["task-id-3"]
    ]
}"""
        
        user_prompt = f"""Task to decompose:
{task}

{chr(10).join([f"{k}: {v}" for k, v in (context or {}).items()]) if context else ""}

Maximum subtasks: {max_subtasks}

Provide the decomposition in the required JSON format."""
        
        try:
            response = await self.llm.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response["content"])
            
            # 解析子任务
            subtasks = []
            for st_data in result.get("subtasks", []):
                subtask = SubTask(
                    id=st_data["id"],
                    name=st_data["name"],
                    description=st_data["description"],
                    task_type=TaskType(st_data.get("task_type", "custom")),
                    dependencies=st_data.get("dependencies", []),
                    estimated_complexity=st_data.get("estimated_complexity", 5),
                    assigned_role=st_data.get("assigned_role", "custom"),
                    context=context or {}
                )
                subtasks.append(subtask)
            
            return TaskDecomposition(
                original_task=task,
                subtasks=subtasks,
                parallel_groups=result.get("parallel_groups", []),
                reasoning=result.get("reasoning", "")
            )
            
        except Exception as e:
            print(f"[Decomposition Error] {str(e)}")
            # 返回简单的分解作为回退
            return self._fallback_decomposition(task, context)
    
    def _fallback_decomposition(self, task: str, context: Optional[Dict]) -> TaskDecomposition:
        """简单的回退分解策略"""
        subtasks = [
            SubTask(
                id="task-1",
                name="Analyze Requirements",
                description=f"Analyze the requirements and scope of: {task[:100]}...",
                task_type=TaskType.ANALYSIS,
                assigned_role="analyst"
            ),
            SubTask(
                id="task-2",
                name="Execute Main Task",
                description=f"Execute the primary task: {task[:100]}...",
                task_type=TaskType.CUSTOM,
                dependencies=["task-1"],
                assigned_role="custom"
            ),
            SubTask(
                id="task-3",
                name="Review Results",
                description="Review and validate the results",
                task_type=TaskType.REVIEW,
                dependencies=["task-2"],
                assigned_role="reviewer"
            )
        ]
        
        return TaskDecomposition(
            original_task=task,
            subtasks=subtasks,
            parallel_groups=[["task-1"], ["task-2"], ["task-3"]],
            reasoning="Fallback decomposition due to LLM error"
        )
    
    def estimate_complexity(self, task: str) -> int:
        """估算任务复杂度 (1-10)"""
        # 基于任务长度和关键词的启发式复杂度估算
        complexity = 5
        
        # 长度因子
        if len(task) > 1000:
            complexity += 2
        elif len(task) > 500:
            complexity += 1
        
        # 关键词因子
        complex_keywords = [
            "research", "analyze", "compare", "evaluate",
            "implement", "design", "architect", "optimize",
            "integrate", "refactor", "debug", "test"
        ]
        
        for keyword in complex_keywords:
            if keyword in task.lower():
                complexity += 0.5
        
        return min(int(complexity), 10)