"""
代码审查示例 - 使用 Agent Swarm 进行多维度代码审查
"""
import asyncio
import sys
sys.path.append('..')

from config.settings import Config
from llm.client import LLMClient
from core.orchestrator import AgentSwarmOrchestrator, AggregationStrategy


# 示例代码
SAMPLE_CODE = '''
def process_user_data(data):
    result = []
    for item in data:
        if item['age'] > 18:
            user = {}
            user['name'] = item['name']
            user['email'] = item['email']
            user['status'] = 'adult'
            result.append(user)
    return result

def calculate_total(orders):
    total = 0
    for order in orders:
        total += order['price'] * order['quantity']
    return total

def save_to_db(data):
    import sqlite3
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO users VALUES ({data['id']}, '{data['name']}')")
    conn.commit()
    conn.close()
'''


async def code_review_example():
    """代码审查示例"""
    
    config = Config.from_env()
    llm = LLMClient(config.llm)
    orchestrator = AgentSwarmOrchestrator(llm, config.swarm, name="CodeReviewSwarm")
    
    task = f"""对以下 Python 代码进行全面审查，从多个维度分析：

代码：
```python
{SAMPLE_CODE}
```

审查维度：
1. 代码质量和可读性
2. 性能和效率
3. 安全性问题
4. 错误处理
5. 最佳实践遵循情况
6. 具体改进建议

请提供详细的审查报告。"""
    
    print("=" * 80)
    print("CODE REVIEW EXAMPLE")
    print("=" * 80)
    print("\nAnalyzing code...\n")
    
    result = await orchestrator.execute(
        task=task,
        strategy=AggregationStrategy.HIERARCHICAL,
        progress_callback=lambda msg: print(f"[PROGRESS] {msg}")
    )
    
    print("\n" + "=" * 80)
    print("CODE REVIEW REPORT")
    print("=" * 80)
    
    if result.aggregated_result:
        print(result.aggregated_result.final_output)
    
    print("\n" + "=" * 80)
    print(f"Execution Time: {result.total_time:.2f}s")
    print(f"Subtasks: {result.metadata.get('subtask_count', 0)}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(code_review_example())