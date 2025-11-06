"""
内存中的会话管理器
负责管理所有临时协作会话的状态，不使用数据库
"""
import uuid
import threading
from datetime import datetime
from typing import Dict, Optional, List


class SessionManager:
    """
    单例模式的会话管理器
    使用线程锁保证并发安全
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化会话存储"""
        self.active_sessions: Dict[str, dict] = {}
        self.session_lock = threading.Lock()

    def create_session(self, initiator: str) -> str:
        """
        创建新的协作会话
        
        Args:
            initiator: 发起者标识（用户名或ID）
            
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        
        with self.session_lock:
            self.active_sessions[session_id] = {
                "session_id": session_id,
                "initiator": initiator,
                "created_at": datetime.now().isoformat(),
                "members": {
                    initiator: {
                        "role": "initiator",
                        "joined_at": datetime.now().isoformat(),
                        "channel_name": None  # 将在 WebSocket 连接时设置
                    }
                },
                "structure": {
                    "folders": [],
                    "files": []
                }
            }
        
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据字典，如果不存在则返回 None
        """
        with self.session_lock:
            return self.active_sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        with self.session_lock:
            return session_id in self.active_sessions

    def add_member(self, session_id: str, member_id: str, 
                   role: str = "viewer", channel_name: str = None) -> bool:
        """
        添加成员到会话
        
        Args:
            session_id: 会话ID
            member_id: 成员标识
            role: 成员角色 (initiator/editor/viewer)
            channel_name: WebSocket 通道名称
            
        Returns:
            成功返回 True，会话不存在返回 False
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            session["members"][member_id] = {
                "role": role,
                "joined_at": datetime.now().isoformat(),
                "channel_name": channel_name
            }
            return True

    def remove_member(self, session_id: str, member_id: str) -> bool:
        """
        从会话中移除成员
        如果是最后一个成员离开，自动销毁会话
        
        Args:
            session_id: 会话ID
            member_id: 成员标识
            
        Returns:
            会话是否被销毁
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            if member_id in session["members"]:
                del session["members"][member_id]
            
            # 如果没有成员了，销毁会话
            if len(session["members"]) == 0:
                del self.active_sessions[session_id]
                return True
            
            return False

    def update_member_channel(self, session_id: str, member_id: str, 
                             channel_name: str) -> bool:
        """
        更新成员的 WebSocket 通道名称
        
        Args:
            session_id: 会话ID
            member_id: 成员标识
            channel_name: WebSocket 通道名称
            
        Returns:
            成功返回 True
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            if member_id in session["members"]:
                session["members"][member_id]["channel_name"] = channel_name
                return True
            
            return False

    def get_member_role(self, session_id: str, member_id: str) -> Optional[str]:
        """
        获取成员角色
        
        Args:
            session_id: 会话ID
            member_id: 成员标识
            
        Returns:
            成员角色，如果不存在返回 None
        """
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return None
            
            member = session["members"].get(member_id)
            return member["role"] if member else None

    def update_member_role(self, session_id: str, member_id: str, 
                          new_role: str) -> bool:
        """
        更新成员角色（仅发起者可调用）
        
        Args:
            session_id: 会话ID
            member_id: 成员标识
            new_role: 新角色 (editor/viewer)
            
        Returns:
            成功返回 True
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            if member_id in session["members"] and member_id != session["initiator"]:
                session["members"][member_id]["role"] = new_role
                return True
            
            return False

    def is_initiator(self, session_id: str, member_id: str) -> bool:
        """检查成员是否为发起者"""
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            return session["initiator"] == member_id

    def can_edit(self, session_id: str, member_id: str) -> bool:
        """
        检查成员是否有编辑权限
        
        Args:
            session_id: 会话ID
            member_id: 成员标识
            
        Returns:
            有权限返回 True
        """
        role = self.get_member_role(session_id, member_id)
        return role in ["initiator", "editor"]

    def update_structure(self, session_id: str, structure: dict) -> bool:
        """
        更新文件夹结构（仅由发起者调用）
        
        Args:
            session_id: 会话ID
            structure: 新的文件夹结构
            
        Returns:
            成功返回 True
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False
            
            self.active_sessions[session_id]["structure"] = structure
            return True

    def get_structure(self, session_id: str) -> Optional[dict]:
        """
        获取文件夹结构
        
        Args:
            session_id: 会话ID
            
        Returns:
            文件夹结构字典
        """
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return None
            return session["structure"]

    def get_all_members(self, session_id: str) -> List[dict]:
        """
        获取会话中的所有成员列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            成员列表
        """
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return []
            
            members = []
            for member_id, member_info in session["members"].items():
                members.append({
                    "member_id": member_id,
                    "role": member_info["role"],
                    "joined_at": member_info["joined_at"]
                })
            return members

    def get_session_count(self) -> int:
        """获取当前活跃会话数量"""
        with self.session_lock:
            return len(self.active_sessions)

    def destroy_session(self, session_id: str) -> bool:
        """
        强制销毁会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            成功返回 True
        """
        with self.session_lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                return True
            return False


# 创建全局单例实例
session_manager = SessionManager()
