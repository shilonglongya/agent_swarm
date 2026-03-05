"""
Agent Swarm Framework - 主入口
DT_Project - 多智能体协作框架
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

from config.settings import Config
from llm.client import LLMClient
from core.orchestrator import AgentSwarmOrchestrator, AggregationStrategy


# 加载环境变量
load_dotenv()


async def run_example():
    """运行示例"""
    print("=" * 60)
    print("Agent Swarm Framework - Demo")
    print("=" * 60)
    
    # 检查 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[Error] 请设置 OPENAI_API_KEY 环境变量")
        print("示例:")
        print("  set OPENAI_API_KEY=your-api-key")
        print("  set OPENAI_BASE_URL=https://api.openai.com/v1 (可选)")
        return
    
    # 初始化配置
    config = Config.from_env()
    print(f"\n[Config]")
    print(f"  LLM Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model}")
    print(f"  Max Sub-agents: {config.swarm.max_sub_agents}")
    print(f"  Max Parallel: {config.swarm.max_parallel_tasks}")
    
    # 初始化 LLM 客户端
    llm = LLMClient(config.llm)
    
    # 检查 LLM 可用性
    print("\n[Health Check]")
    if await llm.is_available():
        print("  LLM: ✓ Available")
    else:
        print("  LLM: ✗ Unavailable")
        print("  请检查 API Key 和网络连接")
        return
    
    # 初始化编排器
    print("\n[Initializing Orchestrator]")
    orchestrator = AgentSwarmOrchestrator(
        llm_client=llm,
        config=config.swarm,
        name="DemoSwarm"
    )
    
    # 示例任务 1: 研究任务
    print("\n" + "=" * 60)
    print("Example 1: Research Task")
    print("=" * 60)
    
    task1 = """研究人工智能在医疗诊断领域的最新进展，包括：
1. 主要的 AI 医疗诊断技术
2. 成功案例和实际应用
3. 面临的挑战和限制
4. 未来发展趋势

请提供一份综合报告。"""
    
    print(f"\nTask: {task1[:100]}...")
    
    result1 = await orchestrator.execute(
        task=task1,
        strategy=AggregationStrategy.SYNTHESIS,
        progress_callback=lambda msg: print(f"  → {msg}")
    )
    
    print(f"\n[Result]")
    print(f"  Status: {result1.status.value}")
    print(f"  Total Time: {result1.total_time:.2f}s")
    print(f"  Subtasks: {result1.metadata.get('subtask_count', 0)}")
    print(f"  Parallel Groups: {result1.metadata.get('parallel_groups', 0)}")
    
    if result1.aggregated_result:
        print(f"\n[Final Output Preview]")
        output = result1.aggregated_result.final_output
        print(output[:500] + "..." if len(output) > 500 else output)
    
    # 示例任务 2: 多步骤分析
    print("\n" + "=" * 60)
    print("Example 2: Multi-step Analysis")
    print("=" * 60)
    
    task2 = """分析 Python 和 JavaScript 在 Web 开发中的优缺点对比。
要求：
1. 性能对比
2. 生态系统对比
3. 学习曲线对比
4. 适用场景分析
5. 给出选择建议"""
    
    print(f"\nTask: {task2}")
    
    result2 = await orchestrator.execute(
        task=task2,
        strategy=AggregationStrategy.HIERARCHICAL,
        progress_callback=lambda msg: print(f"  → {msg}")
    )
    
    print(f"\n[Result]")
    print(f"  Status: {result2.status.value}")
    print(f"  Total Time: {result2.total_time:.2f}s")
    
    if result2.aggregated_result:
        print(f"\n[Final Output Preview]")
        output = result2.aggregated_result.final_output
        print(output[:500] + "..." if len(output) > 500 else output)
    
    # 示例任务 3: 使用流式输出
    print("\n" + "=" * 60)
    print("Example 3: Streaming Output")
    print("=" * 60)
    
    task3 = "用一句话总结人工智能对人类社会的影响"
    
    print(f"\nTask: {task3}")
    print("\n[Streaming Output]:")
    
    async for chunk in orchestrator.execute_stream(task3):
        print(chunk, end="", flush=True)
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("Execution Statistics")
    print("=" * 60)
    
    history = orchestrator.get_history()
    print(f"\nTotal Tasks Executed: {len(history)}")
    
    total_time = sum(r.total_time for r in history)
    avg_time = total_time / len(history) if history else 0
    
    print(f"Total Time: {total_time:.2f}s")
    print(f"Average Time: {avg_time:.2f}s")
    
    pool_stats = orchestrator.get_pool_stats()
    print(f"\n[Pool Statistics]")
    print(f"  Total Agents Created: {pool_stats.get('total_agents', 0)}")
    print(f"  Role Distribution: {pool_stats.get('role_distribution', {})}")
    
    print("\n" + "=" * 60)
    print("Demo Completed!")
    print("=" * 60)


async def interactive_mode():
    """交互模式"""
    print("\n" + "=" * 60)
    print("Agent Swarm - Interactive Mode")
    print("=" * 60)
    print("\n输入 'quit' 退出，'stats' 查看统计")
    
    # 初始化
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[Error] 请设置 API Key")
        return
    
    config = Config.from_env()
    llm = LLMClient(config.llm)
    orchestrator = AgentSwarmOrchestrator(llm, config.swarm)
    
    while True:
        print("\n" + "-" * 60)
        task = input("\nEnter your task: ").strip()
        
        if task.lower() in ['quit', 'exit', 'q']:
            break
        
        if task.lower() == 'stats':
            history = orchestrator.get_history()
            print(f"\nTasks executed: {len(history)}")
            print(f"Pool stats: {orchestrator.get_pool_stats()}")
            continue
        
        if not task:
            continue
        
        print("\n[Executing...]")
        
        try:
            result = await orchestrator.execute(
                task=task,
                strategy=AggregationStrategy.SYNTHESIS,
                progress_callback=lambda msg: print(f"  {msg}")
            )
            
            print(f"\n{'='*60}")
            print("FINAL OUTPUT")
            print(f"{'='*60}\n")
            
            if result.aggregated_result:
                print(result.aggregated_result.final_output)
            else:
                print("No output generated")
            
            print(f"\n{'='*60}")
            print(f"Time: {result.total_time:.2f}s | Status: {result.status.value}")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"[Error] {str(e)}")
    
    print("\nGoodbye!")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Swarm Framework")
    parser.add_argument(
        "--mode",
        choices=["demo", "interactive"],
        default="demo",
        help="运行模式 (默认: demo)"
    )
    parser.add_argument(
        "--provider",
        default=None,
        help="LLM 提供商 (openai, anthropic)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="模型名称"
    )
    
    args = parser.parse_args()
    
    # 更新环境变量
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model
    
    try:
        if args.mode == "interactive":
            asyncio.run(interactive_mode())
        else:
            asyncio.run(run_example())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n[Fatal Error] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()