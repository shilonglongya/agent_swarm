"""
内容创作示例 - 使用 Agent Swarm 进行协作式内容创作
"""
import asyncio
import sys
sys.path.append('..')

from config.settings import Config
from llm.client import LLMClient
from core.orchestrator import AgentSwarmOrchestrator, AggregationStrategy


async def content_creation_example():
    """内容创作示例"""
    
    config = Config.from_env()
    llm = LLMClient(config.llm)
    orchestrator = AgentSwarmOrchestrator(llm, config.swarm, name="ContentSwarm")
    
    task = """创作一篇关于"远程工作的未来"的博客文章。

要求：
1. 标题吸引人且 SEO 友好
2. 引言部分要有吸引力，提出问题或痛点
3. 主体部分包含 3-5 个小节，每个小节有明确的主题
4. 包含实际的数据和案例支持观点
5. 结尾要有行动号召或思考题
6. 语气专业但平易近人
7. 总字数 1500-2000 字
8. 提供 3-5 个推荐标签

目标受众：
- 科技公司管理者
- HR 专业人士
- 远程工作者
- 对远程工作感兴趣的企业主"""
    
    print("=" * 80)
    print("CONTENT CREATION EXAMPLE")
    print("=" * 80)
    print("\nCreating content with collaborative agents...\n")
    
    result = await orchestrator.execute(
        task=task,
        strategy=AggregationStrategy.SYNTHESIS,
        progress_callback=lambda msg: print(f"[PROGRESS] {msg}")
    )
    
    print("\n" + "=" * 80)
    print("GENERATED CONTENT")
    print("=" * 80)
    
    if result.aggregated_result:
        print(result.aggregated_result.final_output)
        
        # 保存到文件
        output_file = "blog_post.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.aggregated_result.final_output)
        print(f"\n[Content saved to {output_file}]")
    
    print("\n" + "=" * 80)
    print(f"Creation Time: {result.total_time:.2f}s")
    print(f"Agents Used: {result.metadata.get('subtask_count', 0)}")
    print("=" * 80)


async def multi_language_example():
    """多语言内容创作示例"""
    
    config = Config.from_env()
    llm = LLMClient(config.llm)
    orchestrator = AgentSwarmOrchestrator(llm, config.swarm, name="MultiLangSwarm")
    
    task = """为一款新的生产力应用创建多语言营销文案。

产品信息：
- 名称: FocusFlow
- 功能: AI 驱动的任务管理、时间追踪、团队协作
- 目标市场: 全球
- 目标用户: 自由职业者、小型团队、项目经理

需要创建：
1. 英文版本（主版本）
2. 中文版本
3. 日文版本
4. 每个版本包含：
   - 30 秒电梯演讲
   - 3 个主要卖点
   - 1 个简短的用户评价
   - CTA（行动号召）

确保每个版本都符合当地文化习惯。"""
    
    print("\n" + "=" * 80)
    print("MULTI-LANGUAGE CONTENT EXAMPLE")
    print("=" * 80)
    
    result = await orchestrator.execute(
        task=task,
        strategy=AggregationStrategy.HIERARCHICAL,
        progress_callback=lambda msg: print(f"[PROGRESS] {msg}")
    )
    
    print("\n" + "=" * 80)
    print("MULTI-LANGUAGE MARKETING COPY")
    print("=" * 80)
    
    if result.aggregated_result:
        print(result.aggregated_result.final_output)
    
    print("\n" + "=" * 80)
    print(f"Execution Time: {result.total_time:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    print("Choose example:")
    print("1. Content Creation")
    print("2. Multi-language Content")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(multi_language_example())
    else:
        asyncio.run(content_creation_example())