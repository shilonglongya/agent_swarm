"""
结果汇总器 - 整合子代理的执行结果
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from llm.client import LLMClient
from core.sub_agent import AgentResult


class AggregationStrategy(Enum):
    """汇总策略"""
    HIERARCHICAL = "hierarchical"  # 分层汇总
    SEQUENTIAL = "sequential"      # 顺序汇总
    PARALLEL = "parallel"          # 并行汇总（简单合并）
    CONSENSUS = "consensus"        # 共识汇总（投票）
    SYNTHESIS = "synthesis"        # 综合汇总（LLM整合）


@dataclass
class AggregatedResult:
    """汇总结果"""
    original_task: str
    final_output: str
    subtask_results: List[AgentResult]
    aggregation_strategy: AggregationStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "original_task": self.original_task,
            "final_output": self.final_output,
            "subtask_results": [r.to_dict() for r in self.subtask_results],
            "aggregation_strategy": self.aggregation_strategy.value,
            "metadata": self.metadata
        }


class ResultAggregator:
    """
    结果汇总器
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def aggregate(
        self,
        original_task: str,
        results: List[AgentResult],
        strategy: AggregationStrategy = AggregationStrategy.SYNTHESIS,
        parallel_groups: Optional[List[List[str]]] = None
    ) -> AggregatedResult:
        """
        汇总子代理结果
        
        Args:
            original_task: 原始任务
            results: 子代理执行结果列表
            strategy: 汇总策略
            parallel_groups: 并行组信息
        
        Returns:
            AggregatedResult 汇总结果
        """
        if strategy == AggregationStrategy.HIERARCHICAL:
            final_output = await self._hierarchical_aggregate(original_task, results)
        elif strategy == AggregationStrategy.SEQUENTIAL:
            final_output = await self._sequential_aggregate(original_task, results)
        elif strategy == AggregationStrategy.PARALLEL:
            final_output = await self._parallel_aggregate(original_task, results)
        elif strategy == AggregationStrategy.CONSENSUS:
            final_output = await self._consensus_aggregate(original_task, results)
        else:  # SYNTHESIS
            final_output = await self._synthesis_aggregate(original_task, results)
        
        # 计算元数据
        metadata = self._compute_metadata(results, parallel_groups)
        
        return AggregatedResult(
            original_task=original_task,
            final_output=final_output,
            subtask_results=results,
            aggregation_strategy=strategy,
            metadata=metadata
        )
    
    async def _synthesis_aggregate(
        self,
        original_task: str,
        results: List[AgentResult]
    ) -> str:
        """综合汇总 - 使用 LLM 智能整合"""
        # 构建结果摘要
        results_summary = []
        for r in results:
            results_summary.append(f"""
Subtask: {r.subtask_id}
Role: {r.metadata.get('role', 'unknown')}
Status: {r.status.value}
Output:
{r.output}
{"Error: " + r.error if r.error else ""}
""")
        
        system_prompt = """You are a Result Aggregation Specialist.
Your role is to synthesize multiple subtask outputs into a coherent, comprehensive final result.

Guidelines:
1. Integrate information from all subtasks logically
2. Resolve any contradictions or conflicts
3. Maintain consistency in style and format
4. Provide a well-structured final output
5. Include insights that emerge from combining the results"""
        
        user_prompt = f"""Original Task:
{original_task}

Subtask Results:
{chr(10).join(results_summary)}

Please synthesize these results into a comprehensive final output."""
        
        try:
            response = await self.llm.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )
            return response["content"]
        except Exception as e:
            # 回退到简单合并
            return self._simple_merge(results)
    
    async def _hierarchical_aggregate(
        self,
        original_task: str,
        results: List[AgentResult]
    ) -> str:
        """分层汇总 - 按角色分组后逐层整合"""
        # 按角色分组
        role_groups: Dict[str, List[AgentResult]] = {}
        for r in results:
            role = r.metadata.get("role", "unknown")
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append(r)
        
        # 每层内部汇总
        layer_outputs = []
        for role, role_results in role_groups.items():
            layer_summary = f"\n## {role.upper()} OUTPUTS\n\n"
            for r in role_results:
                layer_summary += f"### {r.subtask_id}\n{r.output}\n\n"
            layer_outputs.append(layer_summary)
        
        # 最终整合
        combined = "\n".join(layer_outputs)
        
        try:
            response = await self.llm.complete(
                messages=[
                    {"role": "system", "content": "Integrate these role-based outputs into a coherent result."},
                    {"role": "user", "content": f"Task: {original_task}\n\n{combined}"}
                ],
                temperature=0.5
            )
            return response["content"]
        except:
            return combined
    
    async def _sequential_aggregate(
        self,
        original_task: str,
        results: List[AgentResult]
    ) -> str:
        """顺序汇总 - 按依赖顺序逐步整合"""
        # 按子任务ID排序（假设ID包含顺序信息）
        sorted_results = sorted(results, key=lambda r: r.subtask_id)
        
        accumulated = ""
        for i, result in enumerate(sorted_results):
            if i == 0:
                accumulated = result.output
            else:
                # 将当前结果与累积结果整合
                try:
                    response = await self.llm.complete(
                        messages=[
                            {"role": "system", "content": "Merge the previous output with the new subtask output."},
                            {"role": "user", "content": f"Previous: {accumulated}\n\nNew ({result.subtask_id}): {result.output}\n\nProvide merged result."}
                        ],
                        temperature=0.3,
                        max_tokens=2000
                    )
                    accumulated = response["content"]
                except:
                    accumulated += f"\n\n{result.output}"
        
        return accumulated
    
    async def _parallel_aggregate(
        self,
        original_task: str,
        results: List[AgentResult]
    ) -> str:
        """并行汇总 - 简单合并所有输出"""
        return self._simple_merge(results)
    
    async def _consensus_aggregate(
        self,
        original_task: str,
        results: List[AgentResult]
    ) -> str:
        """共识汇总 - 基于投票或一致性"""
        # 提取所有结果的关键点
        all_outputs = [r.output for r in results if r.output]
        
        if not all_outputs:
            return "No valid outputs to aggregate."
        
        # 使用 LLM 找出共识
        try:
            response = await self.llm.complete(
                messages=[
                    {"role": "system", "content": "Find the consensus among these outputs. Identify common points and resolve conflicts by majority or logical reasoning."},
                    {"role": "user", "content": f"Task: {original_task}\n\nOutputs:\n" + "\n---\n".join(all_outputs)}
                ],
                temperature=0.3
            )
            return response["content"]
        except:
            return self._simple_merge(results)
    
    def _simple_merge(self, results: List[AgentResult]) -> str:
        """简单合并所有输出"""
        outputs = []
        for r in results:
            if r.output:
                outputs.append(f"## {r.subtask_id} ({r.metadata.get('role', 'unknown')})\n{r.output}")
        return "\n\n".join(outputs)
    
    def _compute_metadata(
        self,
        results: List[AgentResult],
        parallel_groups: Optional[List[List[str]]]
    ) -> Dict[str, Any]:
        """计算元数据"""
        metadata = {
            "total_subtasks": len(results),
            "completed": sum(1 for r in results if r.status.value == "completed"),
            "failed": sum(1 for r in results if r.status.value == "failed"),
            "total_execution_time": sum(r.execution_time for r in results),
            "avg_execution_time": sum(r.execution_time for r in results) / len(results) if results else 0,
            "total_tokens": {
                "prompt": sum(r.token_usage.get("prompt_tokens", 0) for r in results),
                "completion": sum(r.token_usage.get("completion_tokens", 0) for r in results),
                "total": sum(r.token_usage.get("total_tokens", 0) for r in results)
            }
        }
        
        if parallel_groups:
            metadata["parallel_groups"] = len(parallel_groups)
            metadata["max_parallel"] = max(len(g) for g in parallel_groups) if parallel_groups else 1
        
        return metadata
    
    def format_result_report(self, aggregated: AggregatedResult) -> str:
        """格式化结果报告"""
        report = f"""# Agent Swarm Execution Report

## Task
{aggregated.original_task}

## Summary
- Total Subtasks: {aggregated.metadata.get('total_subtasks', 0)}
- Completed: {aggregated.metadata.get('completed', 0)}
- Failed: {aggregated.metadata.get('failed', 0)}
- Total Time: {aggregated.metadata.get('total_execution_time', 0):.2f}s
- Strategy: {aggregated.aggregation_strategy.value}

## Final Output
{aggregated.final_output}

## Subtask Details
"""
        
        for r in aggregated.subtask_results:
            report += f"\n### {r.subtask_id} ({r.metadata.get('role', 'unknown')})\n"
            report += f"- Status: {r.status.value}\n"
            report += f"- Time: {r.execution_time:.2f}s\n"
            if r.error:
                report += f"- Error: {r.error}\n"
            report += f"\n{r.output[:500]}...\n" if len(r.output) > 500 else f"\n{r.output}\n"
        
        return report
