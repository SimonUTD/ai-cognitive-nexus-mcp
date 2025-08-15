import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

# 从我们刚创建的日志模块导入 logger
from mcp_logger import logger

class SessionManager:
    """负责会话数据的存储、检索和生命周期管理。"""
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"会话Session已初始化于: {self.storage_path}")
        except OSError:
            logger.critical(f"重要：无法在以下位置创建会话存储目录： {storage_path}. 请检查是否已经授权访问.", exc_info=True)
            raise

    def _get_path(self, session_id: str) -> Path:
        if not all(c.isalnum() or c in '-_' for c in session_id):
            raise ValueError(f"无效的 session_id 格式: {session_id}")
        return self.storage_path / f"session-{session_id}.json"

    def _cleanup_old_sessions(self):
        """清理超过24小时的旧会話文件，或已损坏的文件。"""
        try:
            now = datetime.now(timezone.utc)
            expiration_duration = timedelta(hours=24)
            cleaned_count = 0
            for session_file in self.storage_path.glob("session-*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    if session_data and "created_at" in session_data:
                        created_at = datetime.fromisoformat(session_data["created_at"])
                        if now - created_at > expiration_duration:
                            session_file.unlink()
                            cleaned_count += 1
                    else:
                        session_file.unlink()
                        logger.warning(f"删除了一个格式不正确的会话文件: {session_file.name}")

                except (json.JSONDecodeError, IOError, ValueError):
                    session_file.unlink()
                    logger.warning(f"删除了一个损坏或无法解析的会话文件: {session_file.name}")
            
            if cleaned_count > 0:
                logger.info(f"会话清理：删除了 {cleaned_count} 个过期的会话。")
        except Exception as e:
            logger.error(f"会话清理过程中发生严重错误: {e}", exc_info=True)

    def create_session(self, initial_context: Optional[str] = None) -> dict:
        self._cleanup_old_sessions()
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id, "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "initial_args": {"initial_context": initial_context},
            "history": [], "artifacts": {}
        }
        if initial_context:
            session_data["history"].append({"role": "system", "content": f"Session initiated with context: {initial_context}"})
        self.save_session(session_id, session_data)
        logger.info(f"创建了新会话: {session_id}")
        return session_data

    def load_session(self, session_id: str) -> Optional[dict]:
        try:
            path = self._get_path(session_id)
            if not path.exists():
                logger.warning(f"未找到ID {session_id} 对应的会话文件。")
                return None
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, ValueError) as e:
            logger.error(f"无法加载或解析会话，ID: {session_id}, 错误信息: {e}", exc_info=True)
            return None

    def save_session(self, session_id: str, data: dict):
        try:
            path = self._get_path(session_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, ValueError) as e:
            logger.error(f"保存会话ID {session_id} 出错，错误信息: {e}", exc_info=True)
            raise