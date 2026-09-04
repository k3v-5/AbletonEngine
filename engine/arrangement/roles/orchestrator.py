"""
Role Orchestrator:
Controls role entry/exit staging, frequency collision avoidance, and role density.
"""
from typing import Dict, List, Set, Tuple
from engine.arrangement.roles.matrix import RoleMatrix, SectionRoleMap

class RoleOrchestrator:
    """
    Ensures roles enter and exit musically without sudden jarring transitions,
    and detects frequency band competition.
    """
    
    # Frequency registers for role conflict detection
    FREQUENCY_REGISTERS = {
        "sub_bass": "sub",
        "kick": "sub",
        "bass": "low",
        "snare": "mid",
        "clap": "mid",
        "chords": "mid",
        "lead": "high_mid",
        "vocal": "high_mid",
        "arp": "high",
        "hihat_closed": "high",
        "hihat_open": "high",
        "percussion": "mid",
        "pad": "mid_low"
    }

    def __init__(self, role_matrix: RoleMatrix):
        self.role_matrix = role_matrix

    def validate_arrangements(self) -> List[str]:
        """Verify frequency balance and smooth role staging across all sections."""
        warnings = []
        sec_count = len(self.role_matrix.section_roles)
        
        for idx in range(sec_count):
            srm = self.role_matrix.get_section_roles(idx)
            if not srm:
                continue
                
            active = srm.active_roles()
            
            # Check for excessive sub frequency clashing
            sub_count = sum(1 for r in active if self.FREQUENCY_REGISTERS.get(r) == "sub")
            if sub_count > 2:
                warnings.append(f"Section {idx} ({srm.section_type.value}): High sub-bass frequency competition ({sub_count} active sub roles).")
                
            # Stagger entrances: if a section adds > 4 new roles at once, flag for staging
            if idx > 0:
                prev_srm = self.role_matrix.get_section_roles(idx - 1)
                if prev_srm:
                    newly_added = set(active) - set(prev_srm.active_roles())
                    if len(newly_added) > 5 and srm.section_type.value != "drop":
                        warnings.append(f"Section {idx}: Sudden entrance of {len(newly_added)} roles without build or stagger.")
                        
        return warnings

    def apply_staggered_entrances(self, section_idx: int, bar_length: int = 16):
        """Stagger role entries across phrases (e.g. 0-4 bars, 4-8 bars, etc.)."""
        srm = self.role_matrix.get_section_roles(section_idx)
        if not srm or bar_length < 8:
            return
            
        roles = srm.active_roles()
        # Foundation roles (kick, bass) enter bar 0
        # Melodic roles enter bar 4 or 8
        # Secondary percussions enter bar 8 or 12
        for r in roles:
            slot = srm.roles[r]
            if r in ["lead", "vocal"] and bar_length >= 16:
                slot.stagger_bars = 4
            elif r in ["arp", "hihat_open"] and bar_length >= 16:
                slot.stagger_bars = 8
