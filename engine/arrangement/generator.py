"""
Arrangement Generator:
High-level director of song composition and structure generation.
Coordinates Energy Curves, Role Matrix, Multi-Drop Differentiation,
Variation Planning, Repetition Linting, and Compilation.
"""
from typing import Dict, List, Any, Optional
from engine.arrangement.models.song import Song
from engine.arrangement.models.section import Section, SectionType
from engine.arrangement.energy.curve import EnergyCurveGenerator
from engine.arrangement.templates.genres import GenreTemplates
from engine.arrangement.templates.structures import StructureLibrary
from engine.arrangement.roles.matrix import RoleMatrix
from engine.arrangement.roles.orchestrator import RoleOrchestrator
from engine.arrangement.transitions.engine import TransitionEngine
from engine.arrangement.drops.engine import DropDifferentiationEngine
from engine.arrangement.variation.planner import VariationPlanner
from engine.arrangement.linter.linter import ArrangementLinter
from engine.arrangement.scoring import ArrangementScorer
from engine.arrangement.locking import ArrangementLockManager
from engine.arrangement.compiler import ArrangementCompiler

class ArrangementGenerator:
    """Master Arrangement Generator for complete song workflows."""

    def __init__(self, engine_instance):
        self.engine = engine_instance
        self.transition_engine = TransitionEngine()
        self.variation_planner = VariationPlanner()
        self.linter = ArrangementLinter()
        self.lock_manager = ArrangementLockManager()
        self.compiler = ArrangementCompiler(engine_instance)

    def create_song_arrangement(
        self,
        name: str = "New Song",
        genre: str = "melodic_techno",
        duration_seconds: Optional[float] = 300.0,
        target_bars: Optional[int] = None,
        tempo: float = 128.0,
        key: str = "F",
        scale: str = "natural_minor",
        seed: int = 2026,
        structure_name: Optional[str] = None
    ) -> Song:
        """Constructs an intelligent, fully linted and scored Song arrangement."""
        # 1. Derive total bars from target duration
        if target_bars is None:
            # 1 bar = (60 / tempo) * 4 seconds
            bar_duration_sec = (60.0 / tempo) * 4.0
            raw_bars = int(round((duration_seconds or 300.0) / bar_duration_sec))
            # Snap to 16-bar phrase boundary
            target_bars = max(32, ((raw_bars + 8) // 16) * 16)

        # 2. Retrieve section template
        if structure_name and structure_name in StructureLibrary.TEMPLATES:
            raw_sections = StructureLibrary.get_template(structure_name)
        else:
            raw_sections = GenreTemplates.get_genre_template(genre)

        # 3. Scale sections proportionally to fit target_bars
        total_template_bars = sum(s.bars for s in raw_sections)
        scale_factor = target_bars / total_template_bars if total_template_bars > 0 else 1.0
        
        scaled_sections: List[Section] = []
        curr_bar = 0
        for s in raw_sections:
            # Round bars to multiple of 4 or 8
            scaled_b = max(8, int(round((s.bars * scale_factor) / 8.0) * 8))
            scaled_sections.append(Section(
                name=s.name,
                section_type=s.section_type,
                start_bar=curr_bar,
                bars=scaled_b,
                energy=s.energy,
                groove=s.groove
            ))
            curr_bar += scaled_b
            
        # 4. Multi-drop differentiation (Drop 2 > Drop 1)
        scaled_sections = DropDifferentiationEngine.differentiate_drops(scaled_sections)
        
        # 5. Apply multi-dimensional energy curves
        scaled_sections = EnergyCurveGenerator.generate_curve(scaled_sections, template=genre)
        
        # 6. Initialize Role Matrix & Orchestration
        role_matrix = RoleMatrix()
        role_matrix.initialize_for_sections(scaled_sections)
        orchestrator = RoleOrchestrator(role_matrix)
        for idx in range(len(scaled_sections)):
            orchestrator.apply_staggered_entrances(idx, scaled_sections[idx].bars)
            
        # 7. Generate Transitions
        transitions = self.transition_engine.plan_transitions(scaled_sections)
        
        # 8. Create Song model
        song = Song(
            name=name,
            genre=genre,
            tempo=tempo,
            key=key,
            scale=scale,
            sections=scaled_sections,
            role_matrix=role_matrix,
            transitions=transitions,
            seed=seed
        )
        
        return song

    def preview(
        self,
        name: str = "New Song",
        genre: str = "melodic_techno",
        duration_seconds: float = 300.0,
        tempo: float = 128.0,
        key: str = "F",
        scale: str = "natural_minor",
        seed: int = 2026
    ) -> Dict[str, Any]:
        """Generates full preview report without mutating Ableton Live."""
        song = self.create_song_arrangement(
            name=name,
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed
        )
        
        # Lint and Score
        lint_report = self.linter.lint(song.sections)
        score_report = ArrangementScorer.score_arrangement(song.sections)
        
        # Compiler Preview (dry run)
        preview_data = self.compiler.compile(song, preview=True)
        
        preview_data["lint_report"] = lint_report
        preview_data["scoring"] = score_report
        preview_data["transitions"] = [t.to_dict() for t in song.transitions]
        
        return preview_data

    def build(
        self,
        name: str = "New Song",
        genre: str = "melodic_techno",
        duration_seconds: float = 300.0,
        tempo: float = 128.0,
        key: str = "F",
        scale: str = "natural_minor",
        seed: int = 2026,
        compile_to_arrangement: bool = True,
        ensure_sound_sources: bool = True
    ) -> Dict[str, Any]:
        """Builds and executes full song into Ableton Live."""
        song = self.create_song_arrangement(
            name=name,
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed
        )
        
        # Compiler execution (live ACID transaction)
        compile_res = self.compiler.compile(
            song,
            preview=False,
            compile_to_arrangement=compile_to_arrangement,
            ensure_sound_sources=ensure_sound_sources
        )
        
        compile_res["lint_report"] = self.linter.lint(song.sections)
        compile_res["scoring"] = ArrangementScorer.score_arrangement(song.sections)
        return compile_res
