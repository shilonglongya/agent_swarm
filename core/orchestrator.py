"""
Orchestrator 编排器 - Agent Swarm 的核心协调器
DT_Project - 多智能体协作框架
"""
import asyncio
import uuid
import time
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

from llm.client import LLMClient
from config.settings import AgentSwarmConfig
from core.task_decomposer import TaskDecomposer, TaskDecomposition, SubTask
from core.sub_agent import SubAgentPool, AgentResult
from core.result_aggregator import ResultAggregator, AggregationStrategy, AggregatedResult
from core.parallel_executor import ParallelExecutor


class SwarmStatus(Enum):
    """Swarm 状态"""
    IDLE = "idle"
    DECOMPOSING = "decomposing"
    EXECUTING = "executing"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SwarmResult:
    """Swarm 执行结果"""
    task_id: str
    original_task: str
    status: SwarmStatus
    decomposition: Optional[TaskDecomposition] = None
    execution_results: List[AgentResult] = field(default_factory=list)
    aggregated_result: Optional[AggregatedResult] = None
    total_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "original_task": self.original_task,
            "status": self.status.value,
            "decomposition": {
                "subtasks_count": len(self.decomposition.subtasks) if self.decomposition else 0,
                "parallel_groups": len(self.decomposition.parallel_groups) if self.decomposition else 0,
                "reasoning": self.decomposition.reasoning if self.decomposition else ""
            },
            "execution_summary": {
                "total": len(self.execution_results),
                "completed": sum(1 for r in self.execution_results if r.status.value == "completed"),
                "failed": sum(1 for r in self.execution_results if r.status.value == "failed")
            },
            "final_output": self.aggregated_result.final_output if self.aggregated_result else "",
            "total_time": self.total_time,
            "metadata": self.metadata
        }


class AgentSwarmOrchestrator:
    """
    Agent Swarm 编排器
    
    功能:
    - 动态任务分解
    - 并行子代理调度
    - 自适应执行策略
    - 智能结果汇总
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[AgentSwarmConfig] = None,
        name: str = "AgentSwarm"
    ):
        self.name = name
        self.llm = llm_client
        self.config = config or AgentSwarmConfig()
        
        # 初始化组件
        self.decomposer = TaskDecomposer(llm_client, self.config)
        self.agent_pool = SubAgentPool(llm_client, self.config.max_sub_agents)
        self.executor = ParallelExecutor(
            self.agent_pool,
            self.config.max_parallel_tasks,
            self.config.execution_timeout
        )
        self.aggregator = ResultAggregator(llm_client)
        
        # 状态
        self.status = SwarmStatus.IDLE
        self._execution_history: List[SwarmResult] = []
        self._active_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict] = None,
        strategy: AggregationStrategy = AggregationStrategy.SYNTHESIS,
        progress_callback: Optional[Callable[[str], None]] = None,
        streaming: bool = False
    ) -> SwarmResult:
        """
        执行任务（非流式）
        
        Args:
            task: 任务描述
            context: 上下文信息
            strategy: 结果汇总策略
            progress_callback: 进度回调函数
            streaming: 是否使用流式输出
        
        Returns:
            SwarmResult 执行结果
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        def log(msg: str):
            if progress_callback:
                progress_callback(msg)
            if self.config.verbose:
                print(f"[{self.name}] {msg}")
        
        log(f"Task {task_id}: Starting execution")
        log(f"Task: {task[:100]}...")
        
        try:
            # 1. 任务分解
            self.status = SwarmStatus.DECOMPOSING
            log("Phase 1: Task Decomposition")
            
            decomposition = await self.decomposer.decompose(
                task=task,
                context=context,
                max_subtasks=self.config.max_sub_agents
            )
            
            log(f"Decomposed into {len(decomposition.subtasks)} subtasks")
            log(f"Parallel groups: {len(decomposition.parallel_groups)}")
            
            # 2. 并行执行
            self.status = SwarmStatus.EXECUTING
            log("Phase 2: Parallel Execution")
            
            execution_results = await self.executor.execute_parallel_groups(
                subtasks=decomposition.subtasks,
                parallel_groups=decomposition.parallel_groups,
                context=context,
                progress_callback=log if self.config.verbose else None
            )
            
            completed = sum(1 for r in execution_results if r.status.value == "completed")
            failed = sum(1 for r in execution_results if r.status.value == "failed")
            log(f"Execution completed: {completed} succeeded, {failed} failed")
            
            # 3. 结果汇总
            self.status = SwarmStatus.AGGREGATING
            log("Phase 3: Result Aggregation")
            
            aggregated = await self.aggregator.aggregate(
                original_task=task,
                results=execution_results,
                strategy=strategy,
                parallel_groups=decomposition.parallel_groups
            )
            
            log("Aggregation completed")
            
            self.status = SwarmStatus.COMPLETED
            total_time = time.time() - start_time
            
            result = SwarmResult(
                task_id=task_id,
                original_task=task,
                status=SwarmStatus.COMPLETED,
                decomposition=decomposition,
                execution_results=execution_results,
                aggregated_result=aggregated,
                total_time=total_time,
                metadata={
                    "subtask_count": len(decomposition.subtasks),
                    "parallel_groups": len(decomposition.parallel_groups),
                    "completed_subtasks": completed,
                    "failed_subtasks": failed,
                    "parallel_efficiency": self.executor.get_metrics().parallel_efficiency
                }
            )
            
            self._execution_history.append(result)
            log(f"Task {task_id}: Completed in {total_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.status = SwarmStatus.FAILED
            log(f"Task {task_id}: Failed with error: {str(e)}")
            
            return SwarmResult(
                task_id=task_id,
                original_task=task,
                status=SwarmStatus.FAILED,
                metadata={"error": str(e)}
            )
    
    async def execute_stream(
        self,
        task: str,
        context: Optional[Dict] = None,
        strategy: AggregationStrategy = AggregationStrategy.SYNTHESIS
    ) -> AsyncGenerator[str, None]:
        """
        流式执行任务
        
        Yields:
            进度更新和最终结果
        """
        task_id = str(uuid.uuid4())[:8]
        
        yield f"Task {task_id}: Starting...\n"
        
        try:
            # 任务分解
            yield "Decomposing task...\n"
            decomposition = await self.decomposer.decompose(task, context)
            yield f"Decomposed into {len(decomposition.subtasks)} subtasks\n"
            
            # 执行
            yield "Executing subtasks in parallel...\n"
            results = await self.executor.execute_parallel_groups(
                decomposition.subtasks,
                decomposition.parallel_groups,
                context
            )
            
            completed = sum(1 for r in results if r.status.value == "completed")
            yield f"Completed: {completed}/{len(results)}\n"
            
            # 汇总
            yield "Aggregating results...\n"
            aggregated = await self.aggregator.aggregate(
                task, results, strategy, decomposition.parallel_groups
            )
            
            yield "\n=== FINAL OUTPUT ===\n\n"
            yield aggregated.final_output
            
        except Exception as e:
            yield f"Error: {str(e)}\n"
    
    async def execute_with_reflection(
        self,
        task: str,
        context: Optional[Dict] = None,
        max_iterations: int = 3
    ) -> SwarmResult:
        """
        带反思的执行 - 如果失败则重试并改进
        
        Args:
            task: 任务描述
            context: 上下文
            max_iterations: 最大迭代次数
        
        Returns:
            SwarmResult
        """
        best_result = None
        
        for iteration in range(max_iterations):
            print(f"\n[Reflection Iteration {iteration + 1}/{max_iterations}]")
            
            result = await self.execute(
                task=task,
                context=context,
                progress_callback=lambda msg: print(f"  {msg}")
            )
            
            # 检查成功率
            if result.status == SwarmStatus.COMPLETED:
                completed = sum(1 for r in result.execution_results if r.status.value == "completed")
                total = len(result.execution_results)
                success_rate = completed / total if total > 0 else 0
                
                if success_rate >= 0.8:  # 80% 成功率
                    print(f"Success rate: {success_rate:.1%} - Accepting result")
                    return result
                
                print(f"Success rate: {success_rate:.1%} - Will retry with improvements")
                
                # 添加改进建议到上下文
                if context is None:
                    context = {}
                
                failed_tasks = [
                    r.subtask_id for r in result.execution_results
                    if r.status.value == "failed"
                ]
                context["previous_attempt_issues"] = f"Failed subtasks: {failed_tasks}"
                context["iteration"] = iteration + 1
                
                best_result = result
            else:
                if best_result is None:
                    best_result = result
        
        print(f"\nMax iterations reached. Returning best result.")
        return best_result or result
    
    def get_status(self) -> SwarmStatus:
        """获取当前状态"""
        return self.status
    
    def get_history(self) -> List[SwarmResult]:
        """获取执行历史"""
        return self._execution_history
    
    def get_pool_stats(self) -> Dict:
        """获取代理池统计"""
        return self.agent_pool.get_pool_stats()
    
    def clear_history(self):
        """清除执行历史"""
        self._execution_history.clear()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": self.status.value,
            "llm_available": await self.llm.is_available(),
            "pool_stats": self.get_pool_stats(),
            "active_tasks": len(self._active_tasks),
            "history_count": len(self._execution_history)
        }