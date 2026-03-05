"""
Agent Swarm 配置管理
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"  # openai, anthropic, etc.
    api_key: str = ""
    base_url: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv(f"{self.provider.upper()}_API_KEY", "")
        if not self.base_url:
            self.base_url = os.getenv(f"{self.provider.upper()}_BASE_URL")


@dataclass
class AgentSwarmConfig:
    """Agent Swarm 配置"""
    # 编排器设置
    max_sub_agents: int = 100
    max_parallel_tasks: int = 20
    max_iterations: int = 1500
    
    # 任务分解设置
    decomposition_threshold: int = 100  # 任务复杂度阈值
    min_sub_task_size: int = 10
    
    # 执行设置
    execution_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # 结果汇总设置
    aggregation_strategy: str = "hierarchical"  # hierarchical, parallel, sequential
    
    # 日志设置
    verbose: bool = True
    log_level: str = "INFO"
    
    # 代理角色定义
    default_agent_roles: List[Dict] = field(default_factory=lambda: [
        {
            "name": "researcher",
            "description": "Research specialist focused on gathering and analyzing information",
            "system_prompt": "You are a research specialist. Your role is to gather, analyze, and synthesize information accurately and efficiently."
        },
        {
            "name": "analyst",
            "description": "Data analyst specialized in processing and interpreting data",
            "system_prompt": "You are a data analyst. Your role is to process data, identify patterns, and derive meaningful insights."
        },
        {
            "name": "writer",
            "description": "Content creator skilled in producing clear and engaging text",
            "system_prompt": "You are a content writer. Your role is to create clear, engaging, and well-structured content."
        },
        {
            "name": "coder",
            "description": "Software developer proficient in coding and technical implementation",
            "system_prompt": "You are a software developer. Your role is to write clean, efficient, and well-documented code."
        },
        {
            "name": "reviewer",
            "description": "Quality assurance specialist focused on verification and validation",
            "system_prompt": "You are a quality reviewer. Your role is to verify accuracy, check for errors, and ensure high standards."
        }
    ])


@dataclass
class Config:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    swarm: AgentSwarmConfig = field(default_factory=AgentSwarmConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
        )
        
        swarm_config = AgentSwarmConfig(
            max_sub_agents=int(os.getenv("MAX_SUB_AGENTS", "100")),
            max_parallel_tasks=int(os.getenv("MAX_PARALLEL_TASKS", "20")),
            verbose=os.getenv("VERBOSE", "true").lower() == "true"
        )
        
        return cls(llm=llm_config, swarm=swarm_config)


# 全局配置实例
config = Config.from_env()