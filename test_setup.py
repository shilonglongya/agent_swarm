"""
安装验证脚本
"""
import sys
import os

def check_imports():
    """检查所有导入是否正常"""
    print("Checking imports...")
    
    try:
        from config.settings import Config, AgentSwarmConfig
        print("  ✓ config.settings")
        
        from llm.client import LLMClient
        print("  ✓ llm.client")
        
        from core.orchestrator import AgentSwarmOrchestrator
        from core.sub_agent import SubAgent, SubAgentPool
        from core.task_decomposer import TaskDecomposer
        from core.result_aggregator import ResultAggregator
        from core.parallel_executor import ParallelExecutor
        print("  ✓ core modules")
        
        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_env():
    """检查环境变量"""
    print("\nChecking environment variables...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:]
        print(f"  ✓ API Key found: {masked}")
        return True
    else:
        print("  ✗ No API Key found")
        print("  Please set OPENAI_API_KEY")
        return False

def check_structure():
    """检查项目结构"""
    print("\nChecking project structure...")
    
    required_files = [
        "config/__init__.py",
        "config/settings.py",
        "llm/__init__.py",
        "llm/client.py",
        "core/__init__.py",
        "core/orchestrator.py",
        "core/sub_agent.py",
        "core/task_decomposer.py",
        "core/result_aggregator.py",
        "core/parallel_executor.py",
        "main.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_ok = True
    for file in required_files:
        path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(path):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (missing)")
            all_ok = False
    
    return all_ok

def test_llm_connection():
    """测试 LLM 连接"""
    print("\nTesting LLM connection...")
    
    try:
        import asyncio
        from config.settings import Config
        from llm.client import LLMClient
        
        config = Config.from_env()
        llm = LLMClient(config.llm)
        
        async def test():
            return await llm.is_available()
        
        result = asyncio.run(test())
        
        if result:
            print("  ✓ LLM is available")
            return True
        else:
            print("  ✗ LLM is not available")
            print("  Please check your API key and network connection")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Agent Swarm Framework - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Project Structure", check_structure),
        ("Imports", check_imports),
        ("Environment", check_env),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            results.append(check_func())
        except Exception as e:
            print(f"\nError in {name}: {e}")
            results.append(False)
    
    # 如果环境变量检查通过，测试 LLM 连接
    if results[2] if len(results) > 2 else False:
        try:
            results.append(test_llm_connection())
        except Exception as e:
            print(f"\nError testing LLM: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All checks passed!")
        print("\nYou can now run:")
        print("  python main.py")
        return 0
    else:
        print("\n✗ Some checks failed")
        print("\nPlease fix the issues above before running the framework")
        return 1

if __name__ == "__main__":
    sys.exit(main())