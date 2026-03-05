"""
并行执行引擎 - 管理和执行并行子任务
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from core.sub_agent import SubAgent, AgentResult, AgentStatus, SubAgentPool
from core.task_decomposer import SubTask


@dataclass
class ExecutionMetrics:
    """执行指标"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_time: float = 0.0
    critical_path_time: float = 0.0
    parallel_efficiency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_time": self.total_time,
            "critical_path_time": self.critical_path_time,
            "parallel_efficiency": self.parallel_efficiency
        }


class ParallelExecutor:
    """
    并行执行引擎
    """
    
    def __init__(
        self,
        agent_pool: SubAgentPool,
        max_parallel: int = 20,
        timeout: int = 300
    ):
        self.agent_pool = agent_pool
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.metrics = ExecutionMetrics()
        self._execution_log: List[Dict] = []
    
    async def execute_parallel_groups(
        self,
        subtasks: List[SubTask],
        parallel_groups: List[List[str]],
        context: Optional[Dict] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[AgentResult]:
        """
        按并行组执行子任务
        
        Args:
            subtasks: 所有子任务
            parallel_groups: 并行组列表（每组内的任务可并行执行）
            context: 共享上下文
            progress_callback: 进度回调
        
        Returns:
            List[AgentResult] 所有执行结果
        """
        start_time = time.time()
        
        # 构建任务ID到任务的映射
        task_map = {st.id: st for st in subtasks}
        
        # 存储结果
        results: Dict[str, AgentResult] = {}
        completed_task_ids: set = set()
        
        self.metrics.total_tasks = len(subtasks)
        
        if progress_callback:
            progress_callback(f"[Executor] Starting execution of {len(subtasks)} subtasks in {len(parallel_groups)} groups")
        
        # 按组顺序执行
        for group_idx, group in enumerate(parallel_groups):
            if progress_callback:
                progress_callback(f"[Executor] Executing group {group_idx + 1}/{len(parallel_groups)} with {len(group)} tasks")
            
            # 获取当前组的任务
            group_tasks = [task_map[tid] for tid in group if tid in task_map]
            
            # 等待依赖完成
            for task in group_tasks:
                for dep_id in task.dependencies:
                    if dep_id not in completed_task_ids:
                        if progress_callback:
                            progress_callback(f"[Executor] Waiting for dependency: {dep_id}")
                        # 等待依赖完成（这里简化处理，实际应该检查依赖结果）
                        while dep_id not in completed_task_ids:
                            await asyncio.sleep(0.1)
            
            # 并行执行当前组
            group_results = await self._execute_group(
                group_tasks,
                context,
                progress_callback
            )
            
            # 存储结果
            for result in group_results:
                results[result.subtask_id] = result
                if result.status == AgentStatus.COMPLETED:
                    completed_task_ids.add(result.subtask_id)
                    self.metrics.completed_tasks += 1
                elif result.status == AgentStatus.FAILED:
                    self.metrics.failed_tasks += 1
        
        self.metrics.total_time = time.time() - start_time
        
        # 计算关键路径时间（简化版）
        self.metrics.critical_path_time = self._calculate_critical_path_time(
            parallel_groups, results
        )
        
        # 计算并行效率
        if self.metrics.total_time > 0:
            total_task_time = sum(r.execution_time for r in results.values())
            self.metrics.parallel_efficiency = total_task_time / (self.metrics.total_time * len(subtasks)) if subtasks else 0
        
        if progress_callback:
            progress_callback(f"[Executor] Execution completed in {self.metrics.total_time:.2f}s")
        
        return list(results.values())
    
    async def _execute_group(
        self,
        tasks: List[SubTask],
        context: Optional[Dict],
        progress_callback: Optional[Callable[[str], None]]
    ) -> List[AgentResult]:
        """执行一个并行组"""
        
        async def execute_single(task: SubTask) -> AgentResult:
            """执行单个任务"""
            try:
                # 获取代理
                agent = await self.agent_pool.get_or_create_agent(
                    role=task.assigned_role or "custom",
                    system_prompt=None
                )
                
                # 执行任务
                result = await agent.execute(
                    subtask=task,
                    context=context,
                    callback=progress_callback
                )
                
                # 释放代理
                await self.agent_pool.release_agent(agent.agent_id)
                
                return result
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"[Error] Task {task.id}: {str(e)}")
                return AgentResult(
                    subtask_id=task.id,
                    agent_id="error",
                    status=AgentStatus.FAILED,
                    error=str(e)
                )
        
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def execute_with_limit(task: SubTask) -> AgentResult:
            async with semaphore:
                return await execute_single(task)
        
        # 并行执行所有任务
        tasks_with_timeout = [
            asyncio.wait_for(execute_with_limit(task), timeout=self.timeout)
            for task in tasks
        ]
        
        results = await asyncio.gather(*tasks_with_timeout, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentResult(
                    subtask_id=tasks[i].id,
                    agent_id="timeout",
                    status=AgentStatus.FAILED,
                    error=f"Execution failed: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_with_dependency_graph(
        self,
        subtasks: List[SubTask],
        context: Optional[Dict] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[AgentResult]:
        """
        基于依赖图执行子任务（更灵活的执行方式）
        """
        # 构建依赖图
        dependency_graph: Dict[str, set] = {st.id: set(st.dependencies) for st in subtasks}
        task_map = {st.id: st for st in subtasks}
        
        results: Dict[str, AgentResult] = {}
        completed = set()
        in_progress = set()
        
        start_time = time.time()
        self.metrics.total_tasks = len(subtasks)
        
        async def can_execute(task_id: str) -> bool:
            """检查任务是否可以执行（所有依赖已完成）"""
            return dependency_graph[task_id].issubset(completed)
        
        async def execute_task(task_id: str):
            """执行单个任务"""
            if task_id in in_progress or task_id in completed:
                return
            
            in_progress.add(task_id)
            task = task_map[task_id]
            
            try:
                agent = await self.agent_pool.get_or_create_agent(
                    role=task.assigned_role or "custom"
                )
                
                result = await agent.execute(task, context, progress_callback)
                results[task_id] = result
                
                await self.agent_pool.release_agent(agent.agent_id)
                
                if result.status == AgentStatus.COMPLETED:
                    completed.add(task_id)
                    self.metrics.completed_tasks += 1
                else:
                    self.metrics.failed_tasks += 1
                    
            except Exception as e:
                results[task_id] = AgentResult(
                    subtask_id=task_id,
                    agent_id="error",
                    status=AgentStatus.FAILED,
                    error=str(e)
                )
                self.metrics.failed_tasks += 1
            finally:
                in_progress.discard(task_id)
        
        # 主执行循环
        while len(completed) + self.metrics.failed_tasks < len(subtasks):
            # 找出所有可执行的任务
            executable = [
                tid for tid in task_map.keys()
                if tid not in completed and tid not in in_progress
                and await can_execute(tid)
            ]
            
            if not executable and not in_progress:
                # 死锁检测
                remaining = set(task_map.keys()) - completed - set(in_progress)
                if remaining:
                    if progress_callback:
                        progress_callback(f"[Warning] Potential deadlock detected with tasks: {remaining}")
                    # 强制打破死锁
                    for tid in list(remaining)[:self.max_parallel]:
                        executable.append(tid)
                break
            
            # 限制并发数
            to_execute = executable[:self.max_parallel - len(in_progress)]
            
            if to_execute:
                # 并行执行
                await asyncio.gather(*[execute_task(tid) for tid in to_execute])
            else:
                # 等待任务完成
                await asyncio.sleep(0.1)
        
        self.metrics.total_time = time.time() - start_time
        
        return list(results.values())
    
    def _calculate_critical_path_time(
        self,
        parallel_groups: List[List[str]],
        results: Dict[str, AgentResult]
    ) -> float:
        """计算关键路径时间"""
        critical_time = 0.0
        
        for group in parallel_groups:
            # 每组的时间 = 该组中最长的任务
            group_times = [
                results[tid].execution_time
                for tid in group
                if tid in results
            ]
            if group_times:
                critical_time += max(group_times)
        
        return critical_time
    
    def get_metrics(self) -> ExecutionMetrics:
        """获取执行指标"""
        return self.metrics
    
    def get_execution_log(self) -> List[Dict]:
        """获取执行日志"""
        return self._execution_log