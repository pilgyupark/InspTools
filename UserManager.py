from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import yaml



_ACCESS_LEVELS = ["developer", "engineer", "power_user", "user"]
_ACCESS_LEVEL_PRIORITY = {"developer": 4, "engineer": 3, "power_user": 2, "user": 1}


class AccessLevel(Enum):
    """접근 권한 레벨"""
    DEVELOPER = "developer"
    ENGINEER = "engineer"
    POWER_USER = "power_user"
    USER = "user"

    @classmethod
    def from_string(cls, value: str) -> "AccessLevel":
        value_lower = value.lower()
        for level in cls:
            if level.value == value_lower:
                return level
        raise ValueError(f"Unknown access level: {value}")

    def has_access(self, required_level: Optional[str]) -> bool:
        """현재 레벨이 필요한 레벨 이상인지 확인"""
        if not required_level:
            return True
        try:
            required = AccessLevel.from_string(required_level)
            return _ACCESS_LEVEL_PRIORITY[self.value] >= _ACCESS_LEVEL_PRIORITY[required.value]
        except (ValueError, KeyError):
            return True

@dataclass
class User:
    """사용자 정보"""
    username: str = "user1"
    password_hash: str = hashlib.sha256("user1".encode()).hexdigest()
    access_level: str = "user"
    full_name: str = "User1"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(username=data["username"], password_hash=data["password_hash"], access_level=data.get("access_level", "user"), full_name=data.get("full_name", ""),)

    def to_dict(self) -> Dict[str, Any]:
        return {"username": self.username, "password_hash": self.password_hash, "access_level": self.access_level, "full_name": self.full_name,}

    def verify_password(self, password: str) -> bool:
        """비밀번호 확인"""
        return self.password_hash == self._hash_password(password)

    @staticmethod
    def _hash_password(password: str) -> str:
        """비밀번호 해시"""
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def create(cls, username: str, password: str, access_level: str = "user", full_name: str = "") -> "User":
        """새 사용자 생성"""
        return cls(username=username, password_hash=cls._hash_password(password), access_level=access_level, full_name=full_name,)


class UserManager:
    """사용자 관리"""
    def __init__(self, users: Optional[List[User]] = None) -> None:
        self.users: Dict[str, User] = {}
        self.current_user: Optional[User] = None
        if users:
            for user in users:
                self.users[user.username] = user

    def add_user(self, user: User) -> None:
        self.users[user.username] = user

    def authenticate(self, username: str, password: str) -> bool:
        """사용자 인증"""
        if username not in self.users:
            return False
        user = self.users[username]
        if user.verify_password(password):
            self.current_user = user
            return True
        return False

    def logout(self) -> None:
        self.current_user = None

    def get_current_access_level(self) -> Optional[AccessLevel]:
        if self.current_user:
            return AccessLevel.from_string(self.current_user.access_level)
        return None

    @classmethod
    def load_from_yaml(cls, data: List[Dict[str, Any]]) -> "UserManager":
        users = [User.from_dict(item) for item in data]
        return cls(users=users)

    def to_list(self) -> List[Dict[str, Any]]:
        return [user.to_dict() for user in self.users.values()]

    @classmethod
    def load_or_create_from_yaml(cls, yaml_path: str) -> "UserManager":
        from pathlib import Path
        yaml_file = Path(yaml_path)
        if yaml_file.exists():
            with open(yaml_file, "r", encoding="utf-8") as f:
                user_doc = yaml.safe_load(f) or {}
            user_data = user_doc.get("users", []) if isinstance(user_doc, dict) else []
            return cls.load_from_yaml(user_data)
        else:
            manager = cls()
            default_user = User.create(
                username="admin",
                password="admin",
                access_level="developer",
                full_name="Administrator"
            )
            manager.add_user(default_user)
            # 파일에 저장
            yaml_file.parent.mkdir(parents=True, exist_ok=True)
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump({"users": manager.to_list()}, f, sort_keys=False, allow_unicode=True)
            return manager

