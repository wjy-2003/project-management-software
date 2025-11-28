"""
In-memory session manager
Manages temporary collaborative sessions in memory (no database)
"""

import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class SessionManager:
    """
    Singleton session manager
    Uses a thread lock to ensure concurrency safety
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
        """Initialize session storage"""
        self.active_sessions: Dict[str, dict] = {}
        self.session_lock = threading.Lock()

    def create_session(self, initiator: str) -> str:
        """
        Create a new collaboration session

        Args:
            initiator: identifier of the session initiator (username or ID)

        Returns:
            session ID
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
                        "channel_name": None,  # will be set when the WebSocket connects
                    }
                },
                "structure": {"folders": [], "files": []},
            }

        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session information

        Args:
            session_id: session ID

        Returns:
            session data dict, or None if not found
        """
        with self.session_lock:
            return self.active_sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check whether a session exists"""
        with self.session_lock:
            return session_id in self.active_sessions

    def add_member(
        self,
        session_id: str,
        member_id: str,
        role: str = "viewer",
        channel_name: str = None,
    ) -> bool:
        """
        Add a member to a session

        Args:
            session_id: session ID
            member_id: member identifier
            role: member role (initiator/editor/viewer)
            channel_name: WebSocket channel name

        Returns:
            True on success, False if session does not exist
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]
            session["members"][member_id] = {
                "role": role,
                "joined_at": datetime.now().isoformat(),
                "channel_name": channel_name,
            }
            return True

    def remove_member(self, session_id: str, member_id: str) -> bool:
        """
        Remove a member from a session
        If the last member leaves, the session is destroyed

        Args:
            session_id: session ID
            member_id: member identifier

        Returns:
            True if the session was destroyed, False otherwise
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

    def update_member_channel(
        self, session_id: str, member_id: str, channel_name: str
    ) -> bool:
        """
        Update a member's WebSocket channel name

        Args:
            session_id: session ID
            member_id: member identifier
            channel_name: WebSocket channel name

        Returns:
            True on success
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
        Get a member's role

        Args:
            session_id: session ID
            member_id: member identifier

        Returns:
            member role, or None if member/session doesn't exist
        """
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return None

            member = session["members"].get(member_id)
            return member["role"] if member else None

    def update_member_role(
        self, session_id: str, member_id: str, new_role: str
    ) -> bool:
        """
        Update a member's role (only allowed by the initiator)

        Args:
            session_id: session ID
            member_id: member identifier
            new_role: new role (editor/viewer)

        Returns:
            True on success
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
        """Check whether a member is the initiator"""
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            return session["initiator"] == member_id

    def can_edit(self, session_id: str, member_id: str) -> bool:
        """
        Check whether a member has edit permissions

        Args:
            session_id: session ID
            member_id: member identifier

        Returns:
            True if member has edit permissions
        """
        role = self.get_member_role(session_id, member_id)
        return role in ["initiator", "editor"]

    def update_structure(self, session_id: str, structure: dict) -> bool:
        """
        Update folder/file structure (only called by the initiator)

        Args:
            session_id: session ID
            structure: new folder/file structure

        Returns:
            True on success
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                return False

            self.active_sessions[session_id]["structure"] = structure
            return True

    def get_structure(self, session_id: str) -> Optional[dict]:
        """
        Retrieve folder/file structure

        Args:
            session_id: session ID

        Returns:
            structure dict, or None if session not found
        """
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return None
            return session["structure"]

    def get_all_members(self, session_id: str) -> List[dict]:
        """
        Get a list of all members in a session

        Args:
            session_id: session ID

        Returns:
            list of member dicts
        """
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return []

            members = []
            for member_id, member_info in session["members"].items():
                members.append(
                    {
                        "member_id": member_id,
                        "role": member_info["role"],
                        "joined_at": member_info["joined_at"],
                    }
                )
            return members

    def get_session_count(self) -> int:
        """Get the number of active sessions"""
        with self.session_lock:
            return len(self.active_sessions)

    def get_all_sessions(self) -> List[dict]:
        """
        Get a list of all active sessions with basic info

        Returns:
            list of session dicts with id, initiator, created_at, member_count
        """
        with self.session_lock:
            sessions = []
            for session_id, session_data in self.active_sessions.items():
                sessions.append(
                    {
                        "session_id": session_id,
                        "initiator": session_data["initiator"],
                        "created_at": session_data["created_at"],
                        "member_count": len(session_data["members"]),
                    }
                )
            return sessions

    def destroy_session(self, session_id: str) -> bool:
        """
        Forcefully destroy a session

        Args:
            session_id: session ID

        Returns:
            True on success
        """
        with self.session_lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                return True
            return False


# 创建全局单例实例
session_manager = SessionManager()
