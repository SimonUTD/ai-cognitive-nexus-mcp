import os
import json
from pathlib import Path
from collections import deque
from typing import Any, Dict, List, Optional

from mcp_logger import logger
from session_manager import SessionManager
from filelock import FileLock

# --- 全局常量 ---
BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = BASE_DIR / "mcp_sessions"
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_BASE_FILE = DATA_DIR / "knowledge_base.md"
PERSONAS_FILE = DATA_DIR / "personas.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
AGENTS_FILE = DATA_DIR / "agents.json"
TEAMS_FILE = DATA_DIR / "teams.json"

# --- 依赖库导入 ---
try:
    from agno.agent import Agent
    from agno.team.team import Team
    from agno.models.deepseek import DeepSeek
    from agno.models.openai.like import OpenAILike
    from agno.tools.exa import ExaTools
    from agno.tools.thinking import ThinkingTools
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent, Team, DeepSeek, OpenAILike, ExaTools, ThinkingTools = (type(None),) * 6


class ApplicationContext:
    """保存应用程序的状态，包括配置、团队以及所有知识库。"""
    def __init__(self):
        self.session_manager = SessionManager(SESSIONS_DIR)
        self.agents: Dict[str, Any] = {}
        self.teams_config: Dict[str, Any] = {}
        self.teams: Dict[str, Optional[Team]] = {}
        self.personas: Dict[str, Any] = {}
        self.products: Dict[str, Any] = {}
        self.company_knowledge_base: str = ""
        self.factory: Optional[Dict[str, Any]] = None
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        self._load_all_knowledge()
        if AGNO_AVAILABLE:
            self.factory = self._initialize_factory()
            if self.factory:
                self.reinitialize_teams()
        else:
            logger.warning("由于'agno'不可用，跳过AI功能初始化。")

    def _save_data_to_file(self, data: Dict, file_path: Path):
        lock_path = file_path.with_suffix(file_path.suffix + '.lock')
        try:
            with FileLock(lock_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"数据已成功保存至 {file_path}")
        except (IOError, TypeError) as e:
            logger.error(f"数据保存至 {file_path} 失败，原因: {e}", exc_info=True)
            raise
    
    def save_agents(self): self._save_data_to_file(self.agents, AGENTS_FILE)
    def save_teams_config(self): self._save_data_to_file(self.teams_config, TEAMS_FILE)
    def save_personas(self): self._save_data_to_file(self.personas, PERSONAS_FILE)
    def save_products(self): self._save_data_to_file(self.products, PRODUCTS_FILE)

    def _load_file(self, path: Path, is_json: bool) -> Any:
        if not path.exists():
            logger.warning(f"文件在'{path}'路径下未找到。返回空默认值。")
            if is_json:
                self._save_data_to_file({}, path)
                return {}
            return ""
        try:
            with path.open('r', encoding='utf-8') as f:
                return json.load(f) if is_json else f.read()
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"无法加载或解析文件 {path} , 原因: {e}", exc_info=True)
            return {} if is_json else ""

    def _load_all_knowledge(self):
        self.agents = self._load_file(AGENTS_FILE, is_json=True)
        self.teams_config = self._load_file(TEAMS_FILE, is_json=True)
        self.personas = self._load_file(PERSONAS_FILE, is_json=True)
        self.products = self._load_file(PRODUCTS_FILE, is_json=True)
        self.company_knowledge_base = self._load_file(KNOWLEDGE_BASE_FILE, is_json=False)
        logger.info("所有配置文件和数据文件已加载。")

    def _initialize_factory(self) -> Optional[Dict[str, Any]]:
        provider = os.environ.get("LLM_PROVIDER", "deepseek").lower()
        model_map = {
            "deepseek": (DeepSeek, "deepseek-chat", "deepseek-chat"),
            "openailike": (OpenAILike, os.environ.get("OpenAILike_MODEL_ID", "glm-4"), os.environ.get("OpenAILike_AGENT_MODEL_ID", "glm-4"))
        }
        if provider not in model_map:
            logger.error(f"不支持的渠道: '{provider}'.")
            return None
        ModelClass, team_model_id, agent_model_id = model_map[provider]
        kwargs = {}
        if provider == "openailike":
            api_key = os.environ.get("OpenAILike_API_KEY")
            base_url = os.environ.get("OpenAILike_BASE_URL")
            if not api_key or not base_url:
                logger.critical("OpenAILike 服务提供商需要在 .env 文件中设置 OpenAILike_API_KEY 和 OpenAILike_BASE_URL 参数。")
                return None
            kwargs = {"api_key": api_key, "base_url": base_url}
        try:
            agent_model = ModelClass(id=agent_model_id, **kwargs)
            team_model = ModelClass(id=team_model_id, **kwargs)
            logger.info(f"为渠道 '{provider}' 初始化的模型 .")
            return {"agent_model": agent_model, "team_model": team_model, "tool_map": {"ThinkingTools": ThinkingTools(), "ExaTools": ExaTools()}}
        except Exception as e:
            logger.critical(f"Failed to initialize models for provider '{provider}': {e}", exc_info=True)
            return None

    def _create_team_instance(self, team_key: str) -> Optional[Team]:
        if not self.factory: return None
        team_config = self.teams_config.get(team_key, {})
        members = []
        for member_key in team_config.get("members", []):
            if member_key in self.teams_config:
                if self.teams.get(member_key):
                    members.append(self.teams[member_key])
                else:
                    logger.error(f"依赖团队 '{member_key}' (作为 '{team_key}' 的成员) 尚未初始化。请检查拓扑排序。")
                    return None
            elif member_key in self.agents:
                agent_config = self.agents[member_key]
                tools = [self.factory["tool_map"][t] for t in agent_config.get("tools", []) if t in self.factory["tool_map"]]
                agent = Agent(
                    name=agent_config.get("name", member_key), role=agent_config["role"],
                    description=agent_config["description"], tools=tools, model=self.factory["agent_model"],
                    instructions=agent_config.get("instructions"), markdown=True, add_datetime_to_instructions=True,
                )
                members.append(agent)
            else:
                logger.error(f"团队 '{team_key}' 的成员 '{member_key}' 未在 agents.json 或 teams.json 中定义。")
        
        if not members and team_config.get("members"):
            logger.error(f"团队 '{team_key}' 没有有效的成员，无法创建。")
            return None
            
        return Team(
            name=team_config.get("team_name"), mode="coordinate", members=members, model=self.factory["team_model"],
            description=team_config.get("description"), instructions=team_config.get("instructions"),
            success_criteria=team_config.get("success_criteria"), markdown=True, add_datetime_to_instructions=True
        )

    def reinitialize_teams(self) -> bool:
        if not self.factory:
            logger.warning("AI factory 未初始化，无法初始化团队。")
            return False
        self.teams = {}
        logger.info("正在根据最新配置重新初始化所有团队...")
        if not self.teams_config:
            logger.info("未定义任何团队，跳过初始化。")
            return True
        try:
            sorted_team_keys = self._topological_sort(self.teams_config)
            logger.info(f"正确的团队初始化顺序: {sorted_team_keys}")
        except ValueError as e:
            logger.critical(f"由于依赖循环，无法初始化团队: {e}")
            return False
        for team_key in sorted_team_keys:
            team_instance = self._create_team_instance(team_key)
            if team_instance:
                self.teams[team_key] = team_instance
                logger.info(f"团队 '{team_key}' 初始化成功.")
            else:
                logger.error(f"团队 '{team_key}' 初始化失败。")
        logger.info("所有团队已重新初始化。")
        return True

    def _topological_sort(self, team_configs: Dict[str, Any]) -> List[str]:
        adj = {key: [] for key in team_configs}
        in_degree = {key: 0 for key in team_configs}
        for team_key, config in team_configs.items():
            dependencies = {member for member in config.get("members", []) if member in team_configs}
            in_degree[team_key] = len(dependencies)
            for dep_key in dependencies:
                adj[dep_key].append(team_key)
        queue = deque([key for key, degree in in_degree.items() if degree == 0])
        sorted_list = []
        while queue:
            current_team_key = queue.popleft()
            sorted_list.append(current_team_key)
            for dependent_team_key in adj[current_team_key]:
                in_degree[dependent_team_key] -= 1
                if in_degree[dependent_team_key] == 0:
                    queue.append(dependent_team_key)
        if len(sorted_list) == len(team_configs):
            return sorted_list
        else:
            cycle_nodes = {key for key, degree in in_degree.items() if degree > 0}
            raise ValueError(f"在团队依赖关系中检测到一个循环，涉及: {cycle_nodes}")

    def get_running_team(self, team_key: str) -> Optional[Team]:
        return self.teams.get(team_key)

# 在文件末尾创建 app 实例，供主模块导入
logger.info("初始化 ApplicationContext...")
app = ApplicationContext()
logger.info("ApplicationContext 初始化完成.")