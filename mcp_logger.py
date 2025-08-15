import logging
import logging.handlers
import os
from pathlib import Path

def setup_logger():
    """配置并返回一个全局 logger 实例。"""
    log_file_path = Path(__file__).parent / "mcp_server.log"
    
    # 使用 getLogger 获取根 logger 或特定名称的 logger
    logger = logging.getLogger("MCP_Server")
    logger.setLevel(logging.INFO)

    # 如果 logger 已有 handlers，先清空，防止重复添加
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 控制台 handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 文件 handler
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 创建并配置 logger 实例，供其他模块导入
logger = setup_logger()

# 确保日志立即写入文件
for handler in logger.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.flush()