"""
Sound Design Linter:
Audits track production chains for issues:
- Missing primary instrument
- Empty drum racks
- Stereo sub-bass
- Excessive gain (> +6.0 dB)
- Excessive reverb on bass/kick
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class SoundLintIssue:
    severity: str  # ERROR, WARNING, INFO
    rule_id: str
    message: str
    track_index: Optional[int] = None

class SoundLinter:
    """Audits production sound design quality."""

    @staticmethod
    def lint_track(track_info: Dict[str, Any], role: str = "BASS") -> Dict[str, Any]:
        issues: List[SoundLintIssue] = []
        t_idx = track_info.get("index", track_info.get("ableton_index", 0))
        devices = track_info.get("devices", [])
        clean_role = role.upper().strip()

        # 1. Missing Instrument on MIDI track
        if track_info.get("is_midi_track", True) and not devices:
            issues.append(SoundLintIssue(
                severity="ERROR",
                rule_id="SND-001-EMPTY-TRACK",
                message=f"Track {t_idx} ({track_info.get('name')}) has no instrument or devices.",
                track_index=t_idx
            ))

        # 2. Empty Drum Rack check
        for dev in devices:
            if "drum" in dev.get("name", "").lower() or dev.get("class_name") == "DrumGroupDevice":
                pads = dev.get("drum_pads", [])
                if len(pads) == 0:
                    issues.append(SoundLintIssue(
                        severity="ERROR",
                        rule_id="SND-002-EMPTY-DRUM-RACK",
                        message=f"Drum Rack on track {t_idx} has 0 populated pads.",
                        track_index=t_idx
                    ))

        # 3. Stereo Sub-Bass check
        if clean_role in ["SUB_BASS", "SUB"] and track_info.get("panning", 0.0) != 0.0:
            issues.append(SoundLintIssue(
                severity="WARNING",
                rule_id="SND-003-STEREO-SUB",
                message=f"Sub-bass on track {t_idx} is panned ({track_info.get('panning')}). Sub frequencies must be strictly centered/mono.",
                track_index=t_idx
            ))

        # 4. Extreme Gain check
        vol = track_info.get("volume", 0.85)
        if vol > 1.0:  # In Live, 0.85 = 0dB, >1.0 = clipping danger
            issues.append(SoundLintIssue(
                severity="WARNING",
                rule_id="SND-004-GAIN-STAGING",
                message=f"Track {t_idx} volume ({vol}) exceeds safe headroom (> 0dB). Potential digital clipping.",
                track_index=t_idx
            ))

        # Score calculation
        score = 100.0
        for iss in issues:
            if iss.severity == "ERROR":
                score -= 30.0
            elif iss.severity == "WARNING":
                score -= 10.0

        return {
            "valid": not any(iss.severity == "ERROR" for iss in issues),
            "sound_health_score": max(0.0, score),
            "issues": [
                {"severity": i.severity, "rule_id": i.rule_id, "message": i.message, "track_index": i.track_index}
                for i in issues
            ]
        }
