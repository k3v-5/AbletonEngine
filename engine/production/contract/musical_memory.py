# engine/production/contract/musical_memory.py
"""
Musical Memory (Memoria Musical Narrativa):
Elevates engine intelligence beyond checklist compliance.
Connects the temporal narrative axis across the entire song:
- "Qué ocurrió antes"       (Contexto histórico y precedente acústico)
- "Qué significa ahora"     (Impacto perceptual en la sección actual)
- "Qué podría hacer después" (Consecuencia evolutiva hacia la siguiente sección)

Allows the AI to understand WHY an element exists, WHAT happened when it changed,
WHICH other elements reacted to its presence/absence, and HOW its return must be staged.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger("MusicalMemory")


@dataclass
class NarrativeMilestone:
    """A single significant musical event with historical, present, and future consequence."""
    milestone_id: str
    element: str                               # e.g. "Kick 808", "SubLab Bass", "Emotional Piano"
    section: str                               # e.g. "Verse 1", "Hook 2", "Bridge", "Hook 3"
    action: str                                # e.g. "SILENCED", "RETURN", "INTRODUCED", "TEXTURE_EXPANSION"
    what_happened_before: str                  # Historical precedent in prior sections
    what_it_means_now: str                     # Emotional / perceptual reality in this section
    what_could_happen_next: str                # Compositional consequence for upcoming sections
    interdependent_reactions: List[str] = field(default_factory=list) # Reactions triggered in other tracks
    artistic_intent: str = ""                  # Sonic thesis justification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "element": self.element,
            "section": self.section,
            "action": self.action,
            "what_happened_before": self.what_happened_before,
            "what_it_means_now": self.what_it_means_now,
            "what_could_happen_next": self.what_could_happen_next,
            "interdependent_reactions": self.interdependent_reactions,
            "artistic_intent": self.artistic_intent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NarrativeMilestone:
        return cls(
            milestone_id=data.get("milestone_id", ""),
            element=data.get("element", ""),
            section=data.get("section", ""),
            action=data.get("action", ""),
            what_happened_before=data.get("what_happened_before", ""),
            what_it_means_now=data.get("what_it_means_now", ""),
            what_could_happen_next=data.get("what_could_happen_next", ""),
            interdependent_reactions=data.get("interdependent_reactions", []),
            artistic_intent=data.get("artistic_intent", ""),
        )


@dataclass
class MusicalMemory:
    """Narrative causal memory governing the emotional and physical arc of the song."""
    song_id: str
    milestones: List[NarrativeMilestone] = field(default_factory=list)

    def record_milestone(
        self,
        milestone_id: str,
        element: str,
        section: str,
        action: str,
        what_happened_before: str,
        what_it_means_now: str,
        what_could_happen_next: str,
        interdependent_reactions: Optional[List[str]] = None,
        artistic_intent: str = ""
    ) -> NarrativeMilestone:
        """Records a new musical narrative milestone."""
        # Replace if ID exists
        for idx, m in enumerate(self.milestones):
            if m.milestone_id == milestone_id:
                updated = NarrativeMilestone(
                    milestone_id=milestone_id,
                    element=element,
                    section=section,
                    action=action,
                    what_happened_before=what_happened_before,
                    what_it_means_now=what_it_means_now,
                    what_could_happen_next=what_could_happen_next,
                    interdependent_reactions=interdependent_reactions or [],
                    artistic_intent=artistic_intent
                )
                self.milestones[idx] = updated
                return updated

        m = NarrativeMilestone(
            milestone_id=milestone_id,
            element=element,
            section=section,
            action=action,
            what_happened_before=what_happened_before,
            what_it_means_now=what_it_means_now,
            what_could_happen_next=what_could_happen_next,
            interdependent_reactions=interdependent_reactions or [],
            artistic_intent=artistic_intent
        )
        self.milestones.append(m)
        return m

    def query_narrative_context(self, element: str, section: str = "") -> Optional[NarrativeMilestone]:
        """Queries the narrative meaning of an element in a specific section."""
        for m in reversed(self.milestones):
            matches_elem = (element.lower() in m.element.lower()) or (m.element.lower() in element.lower())
            matches_sec = not section or (section.lower() in m.section.lower()) or (m.section.lower() in section.lower())
            if matches_elem and matches_sec:
                return m
        return None

    def get_milestone(self, milestone_id: str) -> Optional[NarrativeMilestone]:
        for m in self.milestones:
            if m.milestone_id == milestone_id:
                return m
        return None

    def get_milestones_for_section(self, section: str) -> List[NarrativeMilestone]:
        """Returns all narrative milestones associated with the specified section."""
        return [m for m in self.milestones if section.lower() in m.section.lower()]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "milestones": [m.to_dict() for m in self.milestones]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MusicalMemory:
        mem = cls(song_id=data.get("song_id", "default_song"))
        for m_data in data.get("milestones", []):
            mem.milestones.append(NarrativeMilestone.from_dict(m_data))
        return mem

    @classmethod
    def scaffold_from_session(cls, song_id: str, session_data: Dict[str, Any]) -> MusicalMemory:
        """Scaffolds narrative memory dynamically from the active session's tracks, sections, and style."""
        design = session_data.get("design", {}) if isinstance(session_data.get("design"), dict) else {}
        genre = str(session_data.get("genre") or design.get("genre") or "contemporary")
        artist = str(design.get("artist") or session_data.get("artist") or "Sovereign Producer")
        if "tyler" in artist.lower() or "neo-soul" in genre.lower():
            return cls.scaffold_for_neo_soul(song_id=song_id)

        mem = cls(song_id=song_id)
        tracks = session_data.get("tracks", [])
        sections = session_data.get("sections", [])
        sec_names = [str(s.get("name", f"Section {i+1}")) for i, s in enumerate(sections)] if sections else ["Intro", "Main Groove", "Bridge", "Climax", "Outro"]
        intro_sec = sec_names[0]
        mid_sec = sec_names[len(sec_names) // 2] if len(sec_names) > 2 else "Bridge"
        climax_sec = sec_names[-2] if len(sec_names) >= 2 else sec_names[-1]

        rhythm_names = [t.get("name", "Drums") for t in tracks if str(t.get("role", "")).upper() in ("DRUMS", "KICK", "BASS", "808_BASS")] or ["Rhythm Section"]
        harm_names = [t.get("name", "Harmonic Bed") for t in tracks if str(t.get("role", "")).upper() in ("KEYS", "PAD", "LEAD", "SYNTH", "GUITAR", "STRINGS")] or ["Harmonic Bed"]

        mem.record_milestone(
            milestone_id="ARRANGEMENT_ESTABLISHMENT",
            element=", ".join(rhythm_names[:2]),
            section=intro_sec,
            action="GROOVE_ANCHOR",
            what_happened_before=f"Inicio del arreglo en estilo {genre} ({artist}).",
            what_it_means_now="Establece el pulso rítmico y la firma tímbrica soberana del tema.",
            what_could_happen_next=f"Evolución armónica y de tensión hacia {mid_sec}.",
            interdependent_reactions=[f"{h} establece el color modal" for h in harm_names[:2]],
            artistic_intent=f"Identidad sonora inmediata fiel a la estética {genre}."
        )
        mem.record_milestone(
            milestone_id="DYNAMIC_CONTRAST_VALLEY",
            element="Rhythm & Low-End",
            section=mid_sec,
            action="DYNAMIC_BREATH",
            what_happened_before="Densidad rítmica sostenida en las secciones previas.",
            what_it_means_now="Apertura de espacio espectral para renovar la atención del oyente.",
            what_could_happen_next=f"Reingreso de impacto completo en {climax_sec}.",
            interdependent_reactions=[f"{h} toma el primer plano" for h in harm_names[:2]],
            artistic_intent="Contraste dinámico orgánico antes del clímax."
        )
        mem.record_milestone(
            milestone_id="CLIMAX_CONVERGENCE",
            element="Full Ensemble",
            section=climax_sec,
            action="CLIMAX_CONVERGENCE",
            what_happened_before=f"Tensión acumulada tras {mid_sec}.",
            what_it_means_now="Convergencia total de capas rítmicas y armónicas con máxima cohesión.",
            what_could_happen_next="Resolución progresiva hacia el cierre de la obra.",
            interdependent_reactions=[f"Cohesión entre {', '.join(rhythm_names[:2])} y {', '.join(harm_names[:2])}"],
            artistic_intent="Clímax musical soberano sin plantillas genéricas."
        )
        return mem

    @classmethod
    def scaffold_for_neo_soul(cls, song_id: str = "tyler_neo_soul") -> MusicalMemory:
        """Scaffolds the narrative memory for the current neo-soul / Tyler production arc."""
        mem = cls(song_id=song_id)

        # Milestone 1: Kick Drop in Hook 2
        mem.record_milestone(
            milestone_id="KICK_DROP_HOOK_2",
            element="808 Kick",
            section="Hook 2",
            action="SILENCED",
            what_happened_before="El Kick anclaba el groove en Verse 1 y Hook 1 junto al Boom Bap Kit.",
            what_it_means_now="Su retiro crea sensación de ingravidez; el bajo SubLab sostiene el fondo mientras el piano expande su peso armónico.",
            what_could_happen_next="Prepara la caída rítmica total en el Bridge.",
            interdependent_reactions=[
                "SubLab XL asume el rol de único motor de graves",
                "Emotional Piano gana prominencia auditiva",
                "Boom Bap Kit queda sin refuerzo subgrave"
            ],
            artistic_intent="Contraste de ingravidez neo-soul antes de la tensión del puente."
        )

        # Milestone 2: Bridge Vacuum
        mem.record_milestone(
            milestone_id="BRIDGE_VACUUM",
            element="Rhythm Section",
            section="Bridge",
            action="MUTED",
            what_happened_before="Hook 2 flotaba sin Kick pero con batería activa.",
            what_it_means_now="Desestabilización total: Kick y Drums se apagan por completo. Silencio percusivo durante 8 compases (32 beats).",
            what_could_happen_next="Genera privación sensorial máxima para que el reingreso en Hook 3 sea catártico.",
            interdependent_reactions=[
                "Foley Texture (polvo de vinilo) avanza a primer plano",
                "Omnisphere Strings sostienen acordes cinemáticos amplios",
                "Emotional Piano toca voicings suspendidos sin resolución"
            ],
            artistic_intent="Vacío previo para maximizar el contraste de explosión dinámica."
        )

        # Milestone 3: Hook 3 Catartic Return
        mem.record_milestone(
            milestone_id="HOOK_3_RETURN",
            element="808 Kick & Boom Bap Kit",
            section="Hook 3",
            action="CATARTIC_RETURN",
            what_happened_before="16 compases acumulados de sequía rítmica parcial y total (Hook 2 y Bridge).",
            what_it_means_now="El bombo y la batería golpean juntos: el impacto no es sólo matemático, es la resolución de la tensión acumulada.",
            what_could_happen_next="Disolución hacia el Outro donde los elementos se desvanecen gradualmente.",
            interdependent_reactions=[
                "SubLab XL y Kick se realinean en el drop",
                "Analog Lab Lead y Emotional Piano resuelven la progresión en Fa# menor",
                "Efecto de release emocional completo en el oyente"
            ],
            artistic_intent="Clímax cíclico crudo con máxima energía contextual."
        )

        return mem

    def to_ascii_summary(self) -> str:
        lines = [
            "MUSICAL MEMORY (MEMORIA MUSICAL CAUSAL Y NARRATIVA)",
            "─────────────────────────────────────────────────────────────────────────────",
            "ARCO TEMPORAL: 'QUÉ OCURRIÓ ANTES' → 'QUÉ SIGNIFICA AHORA' → 'QUÉ HARÁ DESPUÉS'",
            "─────────────────────────────────────────────────────────────────────────────",
        ]
        for m in self.milestones:
            lines.extend([
                f"• [{m.section}] {m.element} → Acción: {m.action}",
                f"  Intención:  {m.artistic_intent}",
                f"  1. ANTES:   {m.what_happened_before}",
                f"  2. AHORA:   {m.what_it_means_now}",
                f"  3. DESPUÉS: {m.what_could_happen_next}",
                f"  Reacciones: {', '.join(m.interdependent_reactions)}",
                ""
            ])
        return "\n".join(lines)
