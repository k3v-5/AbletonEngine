"""
Arrangement Locking Manager:
Allows specific sections or roles to be locked, preserving them completely
during selective regeneration operations.
"""
from typing import Set, Dict, Any

class ArrangementLockManager:
    """Manages locks on sections and musical roles."""
    
    def __init__(self):
        self.locked_sections: Set[int] = set()
        self.locked_roles: Set[str] = set()

    def lock_section(self, section_idx: int):
        self.locked_sections.add(section_idx)

    def unlock_section(self, section_idx: int):
        self.locked_sections.discard(section_idx)

    def lock_role(self, role: str):
        self.locked_roles.add(role.lower())

    def unlock_role(self, role: str):
        self.locked_roles.discard(role.lower())

    def is_section_locked(self, section_idx: int) -> bool:
        return section_idx in self.locked_sections

    def is_role_locked(self, role: str) -> bool:
        return role.lower() in self.locked_roles

    def to_dict(self) -> Dict[str, Any]:
        return {
            "locked_sections": sorted(list(self.locked_sections)),
            "locked_roles": sorted(list(self.locked_roles))
        }
