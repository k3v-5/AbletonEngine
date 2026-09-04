"""
Forensic Causal Inference & Lineage Engine (PIE Phase 7).
Infers causal hypotheses from acoustic observations and injects
deterministic lineage into ProductionGraph (Measurement -> Observation -> Hypothesis).
GUARANTEE: Purely diagnostic / READ-ONLY; never creates Decision or Action nodes.
"""
from typing import List, Dict, Any, Optional, Tuple, Sequence
import uuid

from .models import ForensicEvent, ForensicEventType, CausalHypothesis, Severity, TrackBaseline
from .exceptions import ForensicsIntegrityError

# Optional import of ProductionGraph to avoid hard coupling when run standalone
try:
    from ..production.graph import ProductionGraph
    from ..production.models import ProductionNode, NodeType, EdgeType, Evidence, EvidenceType, ProductionReference
except ImportError:
    ProductionGraph = None
    ProductionNode = None
    NodeType = None
    EdgeType = None
    Evidence = None
    EvidenceType = None
    ProductionReference = None


class CausalityEngine:
    """
    Deterministic causal inference engine correlating acoustic forensic events
    with probable physical/production causes, supporting evidence, and competing explanations.
    """

    @classmethod
    def generate_hypotheses_for_events(
        cls,
        events: Sequence[ForensicEvent],
        baseline: Optional[TrackBaseline] = None,
        track_name: str = "Audio_Track",
    ) -> List[CausalHypothesis]:
        """
        Generates structured causal hypotheses for a list of forensic events.
        Maintains strict separation between Observation (Fact) and Hypothesis (Inference).
        """
        hypotheses: List[CausalHypothesis] = []
        hypo_counter = 1

        for ev in events:
            ev_type = ev.event_type
            hypo_id = f"hyp_{ev_type.lower()}_{hypo_counter:04d}_{int(ev.start_time_seconds * 1000)}ms"
            hypo_counter += 1

            if ev_type in (ForensicEventType.CLIPPING, ForensicEventType.INTER_SAMPLE_PEAK):
                is_isp = ev_type == ForensicEventType.INTER_SAMPLE_PEAK
                tp_val = ev.details.get("true_peak_dbtp", ev.details.get("peak_dbfs", 0.0))
                likely = "Inter-sample peak overshoot during reconstruction" if is_isp else "Digital full-scale saturation (0 dBFS ceiling breach)"
                summary = (
                    f"Signal exceeded {'continuous 0.0 dBTP ceiling' if is_isp else 'digital full scale'} "
                    f"at {ev.start_time_seconds:.3f}s with peak level {tp_val:.2f}."
                )
                supporting = (
                    f"Measured peak level of {tp_val:.2f} dB.",
                    f"Event duration of {ev.duration_seconds * 1000.0:.1f} ms across channel(s) {', '.join(ev.channels)}.",
                    "Lack of headroom margin on output stage."
                )
                competing = (
                    "Uncompressed transient spike from drums or percussion.",
                    "Excessive master or bus limiter drive.",
                    "DAC filter inter-sample reconstruction phenomenon."
                )
                confidence = min(0.95, ev.confidence)

            elif ev_type == ForensicEventType.RESONANCE:
                f_min = ev.frequency_min_hz or 0.0
                f_max = ev.frequency_max_hz or 0.0
                center_f = (f_min + f_max) / 2.0
                peak_db = ev.details.get("peak_dbfs", -10.0)

                if center_f < 160.0:
                    likely = "Sub-bass room mode accumulation or fundamental resonance"
                    competing = ("Kick drum sub harmonic", "Uncontrolled 808 fundamental", "Monitoring room standing wave")
                elif 1000.0 <= center_f <= 4500.0:
                    likely = "Acoustic resonance in critical vocal/lead midrange"
                    competing = ("Microphone proximity peak", "Synthesizer filter resonance", "Comb filtering from reflections")
                else:
                    likely = "Localized high-Q harmonic buildup"
                    competing = ("Distortion harmonic", "Metallic cymbal ring", "Digital saturation peak")

                summary = f"Narrowband persistent energy build-up around {center_f:.1f} Hz ({f_min:.0f}-{f_max:.0f} Hz)."
                supporting = (
                    f"Resonance peak of {peak_db:.1f} dBFS exceeding local spectral threshold.",
                    f"Persistence duration of {ev.duration_seconds * 1000.0:.1f} ms.",
                )
                confidence = min(0.90, ev.confidence)

            elif ev_type == ForensicEventType.MASKING:
                stem_a = ev.details.get("stem_a", "Stem A")
                stem_b = ev.details.get("stem_b", "Stem B")
                dominant = ev.details.get("dominant_stem", stem_a)
                band = ev.details.get("band_name", "spectral")
                delta_db = ev.details.get("mean_delta_db", 0.0)

                likely = f"Dynamic spectral clash in {band} band where {dominant} masks competing stem"
                summary = (
                    f"Simultaneous energetic contention between '{stem_a}' and '{stem_b}' in band {band} "
                    f"with narrow energy difference of {delta_db:.1f} dB."
                )
                supporting = (
                    f"Both stems active simultaneously exceeding activity threshold.",
                    f"Energy delta {delta_db:.1f} dB <= masking threshold.",
                    f"Coincident duration of {ev.duration_seconds * 1000.0:.1f} ms."
                )
                competing = (
                    "Intentional harmonic layering in arrangement.",
                    "Absence of frequency-specific ducking or sidechain compression.",
                    "Unbalanced EQ curves overlapping identical octave range."
                )
                confidence = min(0.92, ev.confidence)

            elif ev_type == ForensicEventType.PHASE_ANOMALY:
                min_corr = ev.details.get("min_correlation", -0.5)
                likely = "Destructive stereo phase cancellation"
                summary = f"Stereo channels exhibit negative correlation ({min_corr:.2f}) causing mono cancellation risk."
                supporting = (
                    f"Stereo correlation dropped to {min_corr:.2f} for {ev.duration_seconds * 1000.0:.1f} ms.",
                    "Significant energy present in both channels simultaneously."
                )
                competing = (
                    "Artificial stereo widener / Haas effect plugin.",
                    "Reversed polarity on one channel.",
                    "Out-of-phase room mic or dual-mic tracking."
                )
                confidence = min(0.95, ev.confidence)

            elif ev_type in (ForensicEventType.CLICK, ForensicEventType.POP):
                is_click = ev_type == ForensicEventType.CLICK
                likely = "Digital buffer glitch or splice boundary impulse" if is_click else "Low-frequency plosive or mechanical transient"
                summary = f"Isolated high-derivative impulse anomaly lasting {ev.duration_seconds * 1000.0:.1f} ms."
                supporting = (
                    f"High discrete derivative ratio ({ev.details.get('surrounding_ratio', 0.0):.1f}x surrounding level).",
                    f"Peak amplitude {ev.details.get('impulse_peak', 0.0):.3f} linear."
                )
                competing = (
                    "Buffer underrun during audio render.",
                    "Non-zero-crossing audio edit cut.",
                    "Microphone plosive / breath pop."
                )
                confidence = min(0.88, ev.confidence)

            elif ev_type == ForensicEventType.DC_OFFSET:
                mean_lin = ev.details.get("dc_offset_linear", 0.0)
                likely = "Asymmetric signal processing or converter DC bias"
                summary = f"Continuous non-zero average DC offset ({mean_lin:.6f} linear)."
                supporting = (
                    f"Persistent mean offset across channel {', '.join(ev.channels)}.",
                    "Reduces available digital headroom."
                )
                competing = (
                    "Analog emulation plugin saturation asymmetry.",
                    "Hardware converter calibration drift.",
                    "Asymmetric synthesized waveform."
                )
                confidence = 0.95

            elif ev_type == ForensicEventType.CHANNEL_LOSS:
                lost_ch = ev.details.get("lost_channel", "Unknown")
                likely = f"Channel drop or extreme pan automation isolating channel {lost_ch}"
                summary = f"Channel {lost_ch} dropped > {ev.details.get('max_imbalance_db', 0.0):.1f} dB relative to companion channel."
                supporting = (
                    f"Sustained imbalance for {ev.duration_seconds * 1000.0:.1f} ms.",
                    "Companion channel remains energetically active."
                )
                competing = (
                    "Deliberate hard pan effect.",
                    "Mono source routed incorrectly into stereo bus.",
                    "Loose connection / corrupted channel stem."
                )
                confidence = 0.90

            elif ev_type == ForensicEventType.DROPOUT:
                likely = "Audio buffer underrun or missing audio splice"
                summary = f"Energy dropped abruptly from active level for {ev.duration_seconds * 1000.0:.1f} ms."
                supporting = (
                    f"Signal dropped to {ev.details.get('min_dropout_dbfs', -90.0):.1f} dBFS.",
                    "Signal recovers to active level after dropout interval."
                )
                competing = (
                    "Mute automation envelope.",
                    "CPU overload / buffer underrun during playback.",
                    "Accidental gap in clip arrangement."
                )
                confidence = 0.85

            else:
                likely = f"Unclassified acoustic anomaly ({ev_type})"
                summary = f"Detected anomaly of type {ev_type} at {ev.start_time_seconds:.2f}s."
                supporting = (f"Duration: {ev.duration_seconds:.3f}s",)
                competing = ("Acoustic transient", "Arrangement feature")
                confidence = 0.50

            hypothesis = CausalHypothesis(
                hypothesis_id=hypo_id,
                likely_cause=likely,
                summary=summary,
                confidence=confidence,
                observation_ids=(ev.event_id,),
                supporting_evidence=supporting,
                competing_explanations=competing,
                details={
                    "event_type": str(ev.event_type),
                    "start_time_seconds": ev.start_time_seconds,
                    "end_time_seconds": ev.end_time_seconds,
                    "channels": list(ev.channels),
                    "event_details": ev.details
                }
            )
            hypotheses.append(hypothesis)

        return hypotheses

    @classmethod
    def inject_into_production_graph(
        cls,
        graph: Any,
        events: Sequence[ForensicEvent],
        hypotheses: Sequence[CausalHypothesis],
        project_id: str = "default_project",
    ) -> List[str]:
        """
        Injects forensic measurements, observations, and causal hypotheses into the
        ProductionGraph, maintaining strict DAG acyclicity and causal lineage.

        INVARIANTS:
        - NEVER creates DECISION or ACTION nodes.
        - Emits MEASUREMENT -> OBSERVATION -> HYPOTHESIS lineage.
        """
        if graph is None or ProductionGraph is None:
            return []

        created_node_ids: List[str] = []
        event_node_map: Dict[str, str] = {}

        # 1. Inject each ForensicEvent as OBSERVATION preceded by MEASUREMENT
        for ev in events:
            meas_node_id = f"prd_meas_forensic_{ev.event_id}"
            meas_node = ProductionNode(
                node_id=meas_node_id,
                node_type=NodeType.MEASUREMENT,
                project_id=project_id,
                payload={
                    "event_type": str(ev.event_type),
                    "start_time_seconds": ev.start_time_seconds,
                    "end_time_seconds": ev.end_time_seconds,
                    "duration_seconds": ev.duration_seconds,
                    "channels": list(ev.channels),
                    "details": ev.details
                },
                confidence=ev.confidence,
                source="engine/forensics",
                metadata={"forensic_event_id": ev.event_id}
            )
            graph.add_node(meas_node)
            created_node_ids.append(meas_node_id)

            obs_node_id = f"prd_obs_forensic_{ev.event_id}"
            obs_node = ProductionNode(
                node_id=obs_node_id,
                node_type=NodeType.OBSERVATION,
                project_id=project_id,
                payload={
                    "event_id": ev.event_id,
                    "event_type": str(ev.event_type),
                    "severity": str(ev.severity),
                    "frequency_min_hz": ev.frequency_min_hz,
                    "frequency_max_hz": ev.frequency_max_hz,
                },
                confidence=ev.confidence,
                parent_nodes=(meas_node_id,),
                source="engine/forensics",
                metadata={"severity": str(ev.severity)}
            )
            graph.add_node(obs_node)
            created_node_ids.append(obs_node_id)
            event_node_map[ev.event_id] = obs_node_id

        # 2. Inject each CausalHypothesis as HYPOTHESIS linked to its OBSERVATIONs
        for hyp in hypotheses:
            hyp_node_id = f"prd_hyp_forensic_{hyp.hypothesis_id}"
            parent_obs = [event_node_map[obs_id] for obs_id in hyp.observation_ids if obs_id in event_node_map]

            hyp_node = ProductionNode(
                node_id=hyp_node_id,
                node_type=NodeType.HYPOTHESIS,
                project_id=project_id,
                payload={
                    "hypothesis_id": hyp.hypothesis_id,
                    "likely_cause": hyp.likely_cause,
                    "summary": hyp.summary,
                    "supporting_evidence": list(hyp.supporting_evidence),
                    "competing_explanations": list(hyp.competing_explanations),
                    "details": hyp.details
                },
                confidence=hyp.confidence,
                parent_nodes=tuple(parent_obs),
                source="engine/forensics",
                metadata={"observation_count": len(hyp.observation_ids)}
            )
            graph.add_node(hyp_node)
            created_node_ids.append(hyp_node_id)

        return created_node_ids

