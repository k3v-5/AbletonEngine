"""
Role Activation Matrix & Energy-to-Role Mapping.
Defines which musical roles are active, muted, or featured per section and energy tier.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from engine.arrangement.models.section import SectionType

# Standard roles across production styles
STANDARD_ROLES = [
    "kick", "bass", "sub_bass", "snare", "clap", "hihat_closed",
    "hihat_open", "percussion", "lead", "chords", "pad", "arp",
    "vocal", "riser", "impact", "fx"
]

# Section role presets: default active roles by section type
DEFAULT_ROLE_PRESETS: Dict[SectionType, List[str]] = {
    SectionType.INTRO: ["pad", "percussion", "hihat_closed", "fx"],
    SectionType.VERSE: ["kick", "bass", "hihat_closed", "pad", "vocal", "percussion"],
    SectionType.BUILD: ["snare", "hihat_closed", "arp", "pad", "riser", "fx"],
    SectionType.DROP: ["kick", "bass", "sub_bass", "snare", "clap", "hihat_closed", "hihat_open", "percussion", "lead", "chords", "arp", "fx"],
    SectionType.BREAKDOWN: ["pad", "chords", "lead", "vocal", "fx"],
    SectionType.OUTRO: ["kick", "bass", "hihat_closed", "pad", "fx"]
}

@dataclass
class RoleSlot:
    role: str
    active: bool = True
    volume_db: float = 0.0
    density_factor: float = 1.0  # 0.0 to 1.5
    variation_profile: str = "standard"  # subtle, dynamic, complex
    stagger_bars: int = 0  # Delayed entry in bars

@dataclass
class SectionRoleMap:
    section_index: int
    section_type: SectionType
    roles: Dict[str, RoleSlot] = field(default_factory=dict)
    
    def is_active(self, role: str) -> bool:
        return self.roles.get(role, RoleSlot(role=role, active=False)).active
    
    def active_roles(self) -> List[str]:
        return [r for r, slot in self.roles.items() if slot.active]
    
    def activate(self, role: str, density: float = 1.0, variation: str = "standard", stagger: int = 0):
        self.roles[role] = RoleSlot(role=role, active=True, density_factor=density, variation_profile=variation, stagger_bars=stagger)
        
    def deactivate(self, role: str):
        if role in self.roles:
            self.roles[role].active = False

class RoleMatrix:
    """Manages role activation across all sections of a song."""
    
    def __init__(self):
        self.section_roles: Dict[int, SectionRoleMap] = {}
        
    def initialize_for_sections(self, sections: list) -> None:
        """Populate initial role activations based on section type and energy."""
        for idx, sec in enumerate(sections):
            role_map = SectionRoleMap(section_index=idx, section_type=sec.section_type)
            # Default roles for section type
            defaults = DEFAULT_ROLE_PRESETS.get(sec.section_type, ["pad", "lead", "bass"])
            
            # Energy adjustment: if energy >= 0.7, activate core rhythmic elements
            active_set = set(defaults)
            if sec.energy >= 0.75:
                active_set.update(["kick", "bass", "lead", "hihat_open"])
            elif sec.energy < 0.4:
                # Remove heavy drums in low-energy sections unless specified
                active_set.difference_update(["kick", "sub_bass"])
                
            for r in STANDARD_ROLES:
                is_act = r in active_set
                # Density scales with energy
                density = 0.5 + (sec.energy * 0.7) if is_act else 0.0
                role_map.roles[r] = RoleSlot(role=r, active=is_act, density_factor=density)
                
            self.section_roles[idx] = role_map

    def get_section_roles(self, section_idx: int) -> Optional[SectionRoleMap]:
        return self.section_roles.get(section_idx)
        
    def to_dict(self) -> Dict[str, any]:
        return {
            str(idx): {
                "active_roles": srm.active_roles(),
                "roles": {r: {"active": slot.active, "density": slot.density_factor} for r, slot in srm.roles.items()}
            }
            for idx, srm in self.section_roles.items()
        }
