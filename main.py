#!/usr/bin/env python3
"""
Unified MCP
"""
import sys
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

# 从新文件中导入核心组件
from mcp_logger import logger
from app_context import app, AGNO_AVAILABLE
from mcp.server.fastmcp import FastMCP

# --- 全局常量 ---
mcp = FastMCP("Unified MCP")

# 各信息 schema 与 必备字段定义
# 人物类
persona_schema = {"name": str, "role": str, "goals": list, "background": str}
persona_required_fields = {"name", "role", "goals"}

# 产品类
product_schema = {"product_name": str, "description": str, "knowledge_base": str}
product_required_fields = {"product_name", "description", "knowledge_base"}

# Agent角色类
agent_schema = {"name": str, "role": str, "description": str, "tools": list, "instructions": str}
agent_required_fields = {"name", "role", "description"}

# 团队类
team_schema = {"team_name": str, "description": str, "members": list, "instructions": str, "success_criteria": str}
team_required_fields = {"team_name", "members"}

# ==============================================
# 辅助工具
# ==============================================
def validate_data(data: dict, schema: dict, required_fields: set) -> Optional[str]:
    """根据 schema 和必需字段校验数据。如果无效则返回错误信息字符串。"""
    missing_fields = required_fields - set(data.keys())
    if missing_fields:
        return f"缺少必需字段: {list(missing_fields)}"
    
    for key, value in data.items():
        if key in schema and not isinstance(value, schema[key]):
            return f"字段 '{key}' 的类型错误，应为 {schema[key].__name__}，但收到了 {type(value).__name__}。"
    return None

# ==============================================
# MCP Tools
# ==============================================
# 会话 mcp 组件
@mcp.tool()
def start_session(initial_context: Optional[str] = None) -> str:
    """创建新的session用于存储和跟踪会话，每个会议或讨论都应该创建一个新的session。"""
    try:
        new_session = app.session_manager.create_session(initial_context=initial_context)
        return json.dumps({
            "message": "新session创建成功.",
            "session_id": new_session["session_id"]
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"创建session失败，错误信息: {e}", exc_info=True)
        return json.dumps({"error": f"创建session失败，错误信息: {e}"})

# 人物类 mcp 组件
@mcp.tool()
def create_persona(persona_key: str, data: dict) -> str:
    """
    根据定义的Schema创建一个新的人物。
    必需字段: 'name'(str), 'role'(str), 'goals'(list of str).
    可选字段: 'background'(str).
    """
    if persona_key in app.personas:
        return json.dumps({"error": f"人物 '{persona_key}' 已存在..."})
    
    # 使用统一的校验函数
    error_msg = validate_data(data, persona_schema, persona_required_fields)
    if error_msg:
        return json.dumps({"error": f"创建人物失败，{error_msg}"})
    
    app.personas[persona_key] = data
    app.save_personas()
    return json.dumps({"status": "success", "message": f"人物 '{persona_key}' 创建成功。"}, ensure_ascii=False)

@mcp.tool()
def list_personas() -> str:
    """
    列出所有可用的人物信息记录，获取人物信息记录的 key 以加载个人信息。
    """
    try:
        if not app.personas:
            return json.dumps({"message": "目前尚未记录任何人物信息。"}, indent=2, ensure_ascii=False)

        persona_list = [
            {
                "persona_key": key,
                "name": data.get("name", "N/A"),
                "role": data.get("role", "N/A"),
                "goals": data.get("goals", "N/A"),
                "profile_summary": data.get("background", "N/A")
            }
            for key, data in app.personas.items()
        ]
        
        return json.dumps(persona_list, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to list personas: {e}", exc_info=True)
        return json.dumps({"error": "An unexpected error occurred while listing personas."})

@mcp.tool()
def get_persona(persona_key: str) -> str:
    """获取指定人物的完整详细信息。"""
    persona_data = app.personas.get(persona_key)
    if not persona_data:
        return json.dumps({"error": f"未找到人物 '{persona_key}'。"})
    return json.dumps(persona_data, indent=2, ensure_ascii=False)

@mcp.tool()
def update_persona(persona_key: str, data: dict) -> str:
    """
    更新一个已存在人物的部分或全部信息。只提供需要修改的字段。
    """
    if persona_key not in app.personas:
        return json.dumps({"error": f"未找到人物 '{persona_key}'，无法更新。"})
    
    # 校验传入字段的合法性
    for key, value in data.items():
        if key not in persona_schema:
            return json.dumps({"error": f"无效字段 '{key}'。允许的字段为: {list(persona_schema.keys())}"})
        # 简单类型校验
        if not isinstance(value, persona_schema[key]):
            return json.dumps({"error": f"字段 '{key}' 的类型错误，应为 {persona_schema[key].__name__}，但收到了 {type(value).__name__}。"})

    app.personas[persona_key].update(data)
    app.save_personas()
    return json.dumps({"status": "success", "message": f"人物 '{persona_key}' 更新成功。"}, ensure_ascii=False)

@mcp.tool()
def delete_persona(persona_key: str) -> str:
    """删除一个指定的人物记录。"""
    if persona_key not in app.personas:
        return json.dumps({"error": f"未找到人物 '{persona_key}'，无法删除。"})
    
    del app.personas[persona_key]
    app.save_personas()
    return json.dumps({"status": "success", "message": f"人物 '{persona_key}' 删除成功。"}, ensure_ascii=False)

# 产品类 mcp 组件

@mcp.tool()
def create_product(product_key: str, data: dict) -> str:
    """
    根据定义的Schema创建一个新产品。
    必需字段: 'product_name'(str), 'description'(str), 'knowledge_base'(str).
    """
    if product_key in app.products:
        return json.dumps({"error": f"产品 '{product_key}' 已存在，请使用 update_product 进行更新。"})
    
    missing_fields = product_required_fields - set(data.keys())
    if missing_fields:
        return json.dumps({"error": f"创建产品失败，缺少必需字段: {list(missing_fields)}"})
    
    app.products[product_key] = data
    app.save_products()
    return json.dumps({"status": "success", "message": f"产品 '{product_key}' 创建成功。"}, ensure_ascii=False)

@mcp.tool()
def list_products() -> str:
    """列出所有已记录的产品。"""
    if not app.products:
        return json.dumps({"message": "目前尚未记录任何产品。"}, indent=2, ensure_ascii=False)
    product_list = [
        {"product_key": key, "product_name": data.get("product_name", "N/A"), "description": data.get("description", "")}
        for key, data in app.products.items()
    ]
    return json.dumps(product_list, indent=2, ensure_ascii=False)

@mcp.tool()
def get_product(product_key: str) -> str:
    """获取指定产品的完整详细信息，包括其知识库。"""
    product_data = app.products.get(product_key)
    if not product_data:
        return json.dumps({"error": f"未找到产品 '{product_key}'。"})
    return json.dumps(product_data, indent=2, ensure_ascii=False)

@mcp.tool()
def update_product(product_key: str, data: dict) -> str:
    """更新一个已存在产品的信息。只提供需要修改的字段。"""
    if product_key not in app.products:
        return json.dumps({"error": f"未找到产品 '{product_key}'，无法更新。"})

    for key, value in data.items():
        if key not in product_schema:
            return json.dumps({"error": f"无效字段 '{key}'。允许的字段为: {list(product_schema.keys())}"})
        if not isinstance(value, product_schema[key]):
            return json.dumps({"error": f"字段 '{key}' 的类型错误，应为 {product_schema[key].__name__}。"})
            
    app.products[product_key].update(data)
    app.save_products()
    return json.dumps({"status": "success", "message": f"产品 '{product_key}' 更新成功。"}, ensure_ascii=False)

@mcp.tool()
def delete_product(product_key: str) -> str:
    """删除一个指定的产品记录及其知识库。"""
    if product_key not in app.products:
        return json.dumps({"error": f"未找到产品 '{product_key}'，无法删除。"})
    
    del app.products[product_key]
    app.save_products()
    return json.dumps({"status": "success", "message": f"产品 '{product_key}' 删除成功。"}, ensure_ascii=False)

# 人物Agent与团队类 mcp 组件

@mcp.tool()
def create_agent(agent_key: str, data: dict) -> str:
    """
    创建一个新的角色(Agent)。
    必需字段: 'name'(str), 'role'(str), 'description'(str).
    可选字段: 'tools'(list of str), 'instructions'(str).
    """
    if agent_key in app.agents:
        return json.dumps({"error": f"角色 '{agent_key}' 已存在。"})
    missing = agent_required_fields - set(data.keys())
    if missing:
        return json.dumps({"error": f"缺少必需字段: {list(missing)}"})
    
    app.agents[agent_key] = data
    app.save_agents()
    app.reinitialize_teams() # 重新构建团队以识别新角色
    return json.dumps({"status": "success", "message": f"角色 '{agent_key}' 创建成功。团队已重新初始化。"}, ensure_ascii=False)

@mcp.tool()
def get_agent(agent_key: str) -> str:
    """获取指定角色的配置信息。"""
    agent_data = app.agents.get(agent_key)
    if not agent_data:
        return json.dumps({"error": f"未找到角色 '{agent_key}'。"})
    return json.dumps(agent_data, indent=2, ensure_ascii=False)

@mcp.tool()
def list_agents() -> str:
    """列出所有已定义的角色(Agent)。"""
    if not app.agents:
        return json.dumps({"message": "尚未定义任何角色。"}, indent=2, ensure_ascii=False)
    return json.dumps([{"agent_key": k, "name": v.get("name"), "role": v.get("role")} for k, v in app.agents.items()], indent=2, ensure_ascii=False)

@mcp.tool()
def update_agent(agent_key: str, data: dict) -> str:
    """更新一个已存在角色的信息。"""
    if agent_key not in app.agents:
        return json.dumps({"error": f"未找到角色 '{agent_key}'。"})
    
    app.agents[agent_key].update(data)
    app.save_agents()
    app.reinitialize_teams() # 角色更新可能影响团队
    return json.dumps({"status": "success", "message": f"角色 '{agent_key}' 更新成功。团队已重新初始化。"}, ensure_ascii=False)

@mcp.tool()
def delete_agent(agent_key: str) -> str:
    """删除一个角色(Agent)。警告：这可能导致依赖此角色的团队失效。"""
    if agent_key not in app.agents:
        return json.dumps({"error": f"未找到角色 '{agent_key}'。"})
    
    del app.agents[agent_key]
    app.save_agents()
    app.reinitialize_teams() # 角色删除必须重载团队
    return json.dumps({"status": "success", "message": f"角色 '{agent_key}' 已删除。团队已重新初始化。"}, ensure_ascii=False)

@mcp.tool()
def create_team(team_key: str, data: dict) -> str:
    """
    创建一个新的团队。
    必需字段: 'team_name'(str), 'members'(list of str, 成员key可以是agent或team).
    可选字段: 'description'(str), 'instructions'(str), 'success_criteria'(str).
    """
    if team_key in app.teams_config:
        return json.dumps({"error": f"团队 '{team_key}' 已存在。"})
    missing = team_required_fields - set(data.keys())
    if missing:
        return json.dumps({"error": f"缺少必需字段: {list(missing)}"})
    
    app.teams_config[team_key] = data
    app.save_teams_config()
    if not app.reinitialize_teams():
        # 如果重载失败（比如有循环依赖），则撤销操作
        del app.teams_config[team_key]
        app.save_teams_config()
        return json.dumps({"error": "团队创建失败，可能是因为引入了循环依赖或无效成员。操作已回滚。"})
        
    return json.dumps({"status": "success", "message": f"团队 '{team_key}' 创建成功并已激活。"}, ensure_ascii=False)

@mcp.tool()
def get_team_config(team_key: str) -> str:
    """获取指定团队的配置信息（非运行实例）。"""
    team_data = app.teams_config.get(team_key)
    if not team_data:
        return json.dumps({"error": f"未找到团队配置 '{team_key}'。"})
    return json.dumps(team_data, indent=2, ensure_ascii=False)

@mcp.tool()
def list_teams() -> str:
    """列出所有已配置的团队。"""
    if not app.teams_config:
        return json.dumps({"message": "尚未配置任何团队。"}, indent=2, ensure_ascii=False)
    
    team_list = []
    for key, config in app.teams_config.items():
        is_active = key in app.teams # 检查团队实例是否成功创建
        team_list.append({
            "team_key": key,
            "team_name": config.get("team_name"),
            "status": "active" if is_active else "inactive (config error)"
        })
    return json.dumps(team_list, indent=2, ensure_ascii=False)

@mcp.tool()
def update_team(team_key: str, data: dict) -> str:
    """更新一个已存在团队的配置。"""
    if team_key not in app.teams_config:
        return json.dumps({"error": f"未找到团队配置 '{team_key}'。"})
    
    original_config = app.teams_config[team_key].copy()
    app.teams_config[team_key].update(data)
    app.save_teams_config()
    if not app.reinitialize_teams():
        app.teams_config[team_key] = original_config
        app.save_teams_config()
        app.reinitialize_teams()
        return json.dumps({"error": "团队更新失败，新配置可能导致错误。操作已回滚。"})

    app.save_teams_config()
    return json.dumps({"status": "success", "message": f"团队 '{team_key}' 更新成功并已重新激活。"}, ensure_ascii=False)

@mcp.tool()
def delete_team(team_key: str) -> str:
    """删除一个团队的配置。"""
    if team_key not in app.teams_config:
        return json.dumps({"error": f"未找到团队配置 '{team_key}'。"})
    
    del app.teams_config[team_key]
    app.save_teams_config()
    app.reinitialize_teams() # 团队删除后必须重载
    return json.dumps({"status": "success", "message": f"团队 '{team_key}' 已删除。"}, ensure_ascii=False)

# 团队讨论类 mcp 组件
@mcp.tool()
async def run_ai_team(team_name: str, prompt: str, session_id: Optional[str] = None, persona_key: Optional[str] = None, product_key: Optional[str] = None) -> str:
    """
    运行指定的AI团队。
    :param team_name: 要运行的团队的key。
    :param prompt: 本次任务的核心指令。
    :param session_id: (可选) 关联的会话ID，用于加载历史记录和保存结果。
    :param persona_key: (可选) 本次任务中AI需要扮演的人物的key。
    :param product_key: (可选) 本次任务关联的产品的key，用于加载特定知识库。
    """
    if not AGNO_AVAILABLE or not app.factory:
        return json.dumps({"error": "程序未正常安装运行库，AI 无法使用."})

    team = app.get_running_team(team_name) # MODIFIED: 使用新的getter
    if not team:
        return json.dumps({"error": f"团队 ‘{team_name}’ 不可用或初始化失败。请检查团队配置和依赖关系。"})


    context_parts = []
    session_data = None
    
    if session_id:
        session_data = app.session_manager.load_session(session_id)
        if session_data:
            history_str = "\n".join([f"Previous {entry['role']}: {entry['content']}" for entry in session_data.get("history", [])])
            if history_str:
                context_parts.append(f"## Session History\n{history_str}")
        else:
            logger.warning(f"无法加载会话 ‘{session_id}’。将继续操作，但不会保留历史记录。")

    if app.company_knowledge_base:
        context_parts.append(f"## Company-Wide Knowledge Base\n{app.company_knowledge_base}")
    if product_key: # MODIFIED: 使用product_key
        product_data = app.products.get(product_key)
        if product_data:
            context_parts.append(f"## Knowledge Base for Product: '{product_data.get('product_name')}'\n{product_data.get('knowledge_base','')}")
    if persona_key: # MODIFIED: 使用persona_key
        persona_data = app.personas.get(persona_key)
        if persona_data:
            profile_text = (f"Role: {persona_data.get('role')}\n"
                            f"Goals: {', '.join(persona_data.get('goals',[]))}\n"
                            f"Background: {persona_data.get('background', 'N/A')}")
            context_parts.append(f"## Persona Profile to Embody: {persona_data.get('name', persona_key)}\n{profile_text}")
    
    context_header = "--- CONTEXTUAL BACKGROUND ---\n" + "\n\n".join(context_parts) if context_parts else ""
    final_prompt = f"{context_header}\n\n--- YOUR CURRENT TASK ---\n{prompt}".strip()

    try:
        logger.info(f"Running team '{team_name}' for session '{session_id or 'None'}'...")
        result = await team.arun(final_prompt)
        content = result.content if hasattr(result, 'content') else str(result)
        response_data = {"status": "completed", "team_name": team_name, "result": content}
        if session_data:
            session_data["history"].append({"role": "user", "content": prompt})
            session_data["history"].append({"role": "assistant", "content": content})
            app.session_manager.save_session(session_id, session_data)
        return json.dumps(response_data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.exception(f"团队 '{team_name}' 执行错误: {e}")
        return json.dumps({"error": f"发生了一个意外错误: {str(e)}"})


# ==============================================
# 5. Application Lifespan and Startup
# ==============================================
@asynccontextmanager
async def app_lifespan(mcp_instance: FastMCP) -> AsyncIterator[None]:
    """管理应用程序的启动和关闭流程."""
    logger.info("服务器正在运行。应用程序上下文已就绪。")
    yield
    logger.info("服务器正在关闭.")

def main():
    mcp.lifespan = app_lifespan
    logger.info("Unified MCP Server starting...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"服务器执行过程中发生致命错误: {e}", exc_info=True)
        sys.exit(1)
