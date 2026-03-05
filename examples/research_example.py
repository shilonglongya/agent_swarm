"""
研究任务示例 - 使用 Agent Swarm 进行多维度研究
"""
import asyncio
import sys
sys.path.append('..')

from config.settings import Config
from llm.client import LLMClient
from core.orchestrator import AgentSwarmOrchestrator, AggregationStrategy


async def research_example():
    """研究任务示例"""
    
    # 初始化
    config = Config.from_env()
    llm = LLMClient(config.llm)
    orchestrator = AgentSwarmOrchestrator(llm, config.swarm, name="ResearchSwarm")
    
    # 复杂研究任务
    task = """研究并撰写一份关于"量子计算在金融领域应用"的综合报告。

需要涵盖的方面：
1. 量子计算基础技术概述
2. 金融领域的具体应用场景（风险管理、投资组合优化、欺诈检测等）
3. 当前主要的量子计算平台和工具
4. 成功案例和试点项目
5. 技术挑战和限制
6. 未来 5-10 年的发展预测
7. 对金融机构的建议

要求：
- 内容专业且易于理解
- 包含具体的数据和案例
- 结构清晰，有明确的章节划分
- 总字数不少于 2000 字"""
    
    print("=" * 80)
    print("RESEARCH TASK EXAMPLE")
    print("=" * 80)
    print(f"\nTask:\n{task}\n")
    print("=" * 80)
    
    # 执行
    result = await orchestrator.execute(
        task=task,
        strategy=AggregationStrategy.SYNTHESIS,
        progress_callback=lambda msg: print(f"[PROGRESS] {msg}")
    )
    
    # 输出结果
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Status: {result.status.value}")
    print(f"Total Time: {result.total_time:.2f}s")
    print(f"Subtasks: {result.metadata.get('subtask_count', 0)}")
    print(f"Parallel Groups: {result.metadata.get('parallel_groups', 0)}")
    print(f"Completed: {result.metadata.get('completed_subtasks', 0)}")
    print(f"Failed: {result.metadata.get('failed_subtasks', 0)}")
    print(f"Parallel Efficiency: {result.metadata.get('parallel_efficiency', 0):.2%}")
    
    if result.decomposition:
        print("\n" + "=" * 80)
        print("TASK DECOMPOSITION")
        print("=" * 80)
        print(f"Reasoning: {result.decomposition.reasoning}\n")
        
        for i, subtask in enumerate(result.decomposition.subtasks, 1):
            print(f"{i}. [{subtask.assigned_role}] {subtask.name}")
            print(f"   Type: {subtask.task_type.value}")
            print(f"   Complexity: {subtask.estimated_complexity}/10")
            if subtask.dependencies:
                print(f"   Dependencies: {', '.join(subtask.dependencies)}")
            print()
    
    if result.aggregated_result:
        print("\n" + "=" * 80)
        print("FINAL OUTPUT")
        print("=" * 80)
        print(result.aggregated_result.final_output)
        
        # 保存到文件
        output_file = "research_output.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.aggregated_result.final_output)
        print(f"\n[Output saved to {output_file}]")


if __name__ == "__main__":
    asyncio.run(research_example())