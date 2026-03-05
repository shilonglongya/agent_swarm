"""
Agent Swarm Framework
DT_Project - 多智能体协作框架

功能特性:
- 动态任务分解
- 并行子代理执行
- 智能结果汇总
- 支持多种 LLM 提供商
"""

__version__ = "1.0.0"
__author__ = "DT_Project Team"

from core.orchestrator import AgentSwarmOrchestrator
from core.sub_agent import SubAgent, SubAgentPool
from core.task_decomposer import TaskDecomposer
from core.result_aggregator import ResultAggregator, AggregationStrategy
from llm.client import LLMClient
from config.settings import Config

__all__ = [
    "AgentSwarmOrchestrator",
    "SubAgent",
    "SubAgentPool",
    "TaskDecomposer",
    "ResultAggregator",
    "AggregationStrategy",
    "LLMClient",
    "Config"
]