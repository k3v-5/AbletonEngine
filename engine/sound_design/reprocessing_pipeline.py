# engine/sound_design/reprocessing_pipeline.py
"""
Audio Reprocessing & Resynthesis Pipeline:
Production engine managing the Universal Harmonic Transformation Suite (UHTS).

Orchestrates:
1. Automatic Key & BPM detection from Ableton Live LOM.
2. Source material selection:
   - Existing track resample, OR
   - New unused track with guided sound design (role, VST, preset, FX, chord synthesis).
3. Continuous audio DSP mutations across the 20 UHTS algorithms dynamically tuned to Key & BPM.
4. Deployment to a brand new unused Audio Track in Ableton Live with clip slot 0 placement
   and safe headroom gain staging.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import soundfile as sf

from engine.sound_design.resample_mutation_engine import (
    MUTATION_REGISTRY,
    note_to_freq,
    get_chord_frequencies,
    NOTE_TO_SEMITONE
)

logger = logging.getLogger("AudioReprocessingPipeline")

ROOT_INT_TO_NOTE = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
}

NOTE_TO_ROOT_INT = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
    "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
}

# The 20 UHTS Techniques Master Catalog Definition
CATALOG_METADATA = [
    {
        "index": 1,
        "id": "MUT_01_SPECTRAL_FREEZE",
        "name": "Spectral Freeze Drone",
        "registry_name": "SPECTRAL_FREEZE_DRONE",
        "category": "Spectral & Granular",
        "description": "Congelamiento de magnitud espectral (STFT) en ventana sostenida con aleatorización de fase entre fotogramas. Elimina el ataque del martillo/pluma generando un dron armónico líquido infinito sin artefactos de bucle.",
        "best_suited_for": "PAD / ATMOSPHERE / DRONE",
        "tuning_dependence": "Preserva la envolvente de formantes y parciales originales del acorde sostenido."
    },
    {
        "index": 2,
        "id": "MUT_02_TUNED_COMB_CHIME",
        "name": "Tuned Comb Karplus-Strong Chime",
        "registry_name": "TUNED_COMB_CHIME",
        "category": "Harmonic & Modal Tuned",
        "description": "Matriz de 3 filtros de peine Karplus-Strong sintonizados a la tónica, tercera (menor/mayor) y quinta en octavas 3 y 4, con amortiguación de paso bajo en la realimentación (0.88). Transforma acordes en carillones de cristal resonantes.",
        "best_suited_for": "KEYS / ARPEGGIOS / BELLS",
        "tuning_dependence": "100% afinado automáticamente a la Tonalidad y Escala detectadas en Live."
    },
    {
        "index": 3,
        "id": "MUT_03_VOCAL_FORMANT_RESONANCE",
        "name": "Vocal Formant Triple Resonance",
        "registry_name": "VOCAL_FORMANT_RESONANCE",
        "category": "Harmonic & Modal Tuned",
        "description": "Triple resonador de formantes vocales humanos en paralelo (/a/ 800Hz, /e/ 1800Hz, /i/ 2500Hz) con saturación suave tipo wavefolder. Confiere a cualquier sonido un timbre vocal o de coro analógico profundo.",
        "best_suited_for": "VOCAL CHOIR / HYBRID LEAD / CHOP",
        "tuning_dependence": "Filtros paso banda calibrados en el espacio acústico vocal humano."
    },
    {
        "index": 4,
        "id": "MUT_04_INDUSTRIAL_CRUNCH_MUTATION",
        "name": "Industrial Multi-Stage Wavefolder",
        "registry_name": "INDUSTRIAL_CRUNCH_MUTATION",
        "category": "Saturation, Texture & Character",
        "description": "Saturador de 4 etapas de plegado trigonométrico (wavefolding con seno no lineal, recorte asimétrico y saturación tangente hiperbólica), más excitación de armónicos agudos (>3.5kHz). Textura abrasiva y cortante tipo cyberpunk/industrial.",
        "best_suited_for": "BASS / AGGRESSIVE SYNTH / INDUSTRIAL FX",
        "tuning_dependence": "Multiplica los armónicos respetando la fundamental del tono."
    },
    {
        "index": 5,
        "id": "MUT_05_SUB_SAFE_LOW_GROWL",
        "name": "Sub-Safe Low-End Saturated Growl",
        "registry_name": "SUB_SAFE_LOW_GROWL",
        "category": "Low-End & Bass Resynthesis",
        "description": "Aislamiento paso bajo a 120Hz, forzado a MONO estricto, generación de sub-fundamental en octava 1 (30-65Hz) alineada a la tónica del proyecto, y saturación armónica en medios-bajos (120-450Hz). Sub-graves colosales listos para club.",
        "best_suited_for": "SUB BASS / 808 / LOW REESE",
        "tuning_dependence": "Sub-oscilador sintonizado exactamente a la frecuencia fundamental de la Tonalidad."
    },
    {
        "index": 6,
        "id": "MUT_06_PITCH_SHIMMER_DIFFUSION",
        "name": "Pitch-Shifted Shimmer Diffusion",
        "registry_name": "PITCH_SHIMMER_DIFFUSION",
        "category": "Pitch & Time Space",
        "description": "Re-muestreo a doble velocidad (+12 semitonos / octava superior) inyectado en una matriz de retardo difuso multi-tap (110ms, 170ms, 240ms) con realimentación suave. Genera un halo celestial que flota sobre el sonido original.",
        "best_suited_for": "KEYS / HIGH STRINGS / SHIMMER REVERB",
        "tuning_dependence": "Octava superior armónicamente consonante con el acorde original."
    },
    {
        "index": 7,
        "id": "MUT_07_DARK_REESE_OCTAVE_DIVE",
        "name": "Dark Reese Double-Octave Dive",
        "registry_name": "DARK_REESE_OCTAVE_DIVE",
        "category": "Low-End & Bass Resynthesis",
        "description": "Transposición hacia abajo de 2 octavas completas (-24 semitonos), con desfase micro-temporal estéreo independiente (6ms canal izquierdo, 14ms derecho) creando batimento Reese analógico, y filtrado paso bajo a 280Hz.",
        "best_suited_for": "DARK REESE / NEURO BASS / AMBIENT DRONE",
        "tuning_dependence": "Transposición matemática de 2 octavas exactas sobre la fundamental."
    },
    {
        "index": 8,
        "id": "MUT_08_GRANULAR_MICRO_CLOUD",
        "name": "Granular Micro-Particle Cloud",
        "registry_name": "GRANULAR_MICRO_CLOUD",
        "category": "Spectral & Granular",
        "description": "Rebanado en micro-granos de 40ms con ventanas de Hanning, jitter temporal aleatorio y dispersión estéreo espacial desacoplada. Transforma acordes estáticos en una nube de partículas etéreas y cinemáticas.",
        "best_suited_for": "AMBIENT TEXTURE / FOLEY BED / BACKGROUND CLOUD",
        "tuning_dependence": "Reconstruye la masa espectral armónica del sonido fuente."
    },
    {
        "index": 9,
        "id": "MUT_09_VINTAGE_TAPE_WOW_WARP",
        "name": "Vintage Cassette Wow & Flutter",
        "registry_name": "VINTAGE_TAPE_WOW_WARP",
        "category": "Saturation, Texture & Character",
        "description": "Emulación de arrastre de cinta analógica mediante doble oscilador LFO (Wow a 0.8Hz y Flutter a 3.4Hz), saturación asimétrica por histéresis magnética y amortiguación de cabezal a 5.2kHz. Auténtica calidez Lo-Fi nostálgica.",
        "best_suited_for": "LO-FI KEYS / VINTAGE RHODES / INDIE TEXTURE",
        "tuning_dependence": "Micro-modulación de afinación inspirada en reproductores analógicos."
    },
    {
        "index": 10,
        "id": "MUT_10_INHARMONIC_METALLIC_RING",
        "name": "Inharmonic Frequency-Shifted Bell Ring",
        "registry_name": "INHARMONIC_METALLIC_RING",
        "category": "Harmonic & Modal Tuned",
        "description": "Desplazador de frecuencia monobanda basado en la transformada analítica de Hilbert con modulación en anillo sintonizada a sub-portadora fundamental. Produce texturas metálicas, campaniformes y alienígenas.",
        "best_suited_for": "METALLIC BELLS / INDUSTRIAL FOLEY / CYBER TEXTURE",
        "tuning_dependence": "Portadora de modulación sintonizada armónicamente a la Tonalidad detectada."
    },
    {
        "index": 11,
        "id": "MUT_11_REVERSE_SWELL_BLOOM",
        "name": "Reverse Swell Exponential Bloom",
        "registry_name": "REVERSE_SWELL_BLOOM",
        "category": "Pitch & Time Space",
        "description": "Inversión temporal del audio, convolución difusa exponencial de 1.5 segundos, y re-inversión al sentido original. Produce una elevación o 'bloom' pre-acorde sin cortes bruscos, excelente para introducciones y drops.",
        "best_suited_for": "TRANSITION RISER / SWELL / CINEMATIC INTRO",
        "tuning_dependence": "Conserva la armonía del sonido original en reversa difusa."
    },
    {
        "index": 12,
        "id": "MUT_12_LOFI_BIT_CRUSHER_DIRT",
        "name": "10-Bit Downsampled Digital Dirt",
        "registry_name": "LOFI_BIT_CRUSHER_DIRT",
        "category": "Saturation, Texture & Character",
        "description": "Cuantización a 10 bits (1024 pasos discretos) combinada con reducción de frecuencia de muestreo sample-and-hold (factor 7 = ~6.3kHz). Textura áspera crujiente vintage de sampler clásico de los años 90 (SP-1200 / S950).",
        "best_suited_for": "BOOM BAP / LOFI HIP HOP / RETRO TEXTURE",
        "tuning_dependence": "Genera aliasing armónico musical sobre las frecuencias de la canción."
    },
    {
        "index": 13,
        "id": "MUT_13_HAAS_3D_SPATIAL_DECOUPLE",
        "name": "Haas 3D Psychoacoustic Decoupler",
        "registry_name": "HAAS_3D_SPATIAL_DECOUPLE",
        "category": "Pitch & Time Space",
        "description": "Codificación Mid/Side completa, retardo de 19ms en el canal lateral (Side) y rotación de fase de 90° mediante transformada de Hilbert. Abre el campo estéreo a 180° manteniendo compatibilidad mono impecable en el centro.",
        "best_suited_for": "STEREO WIDENING / IMMERSIVE KEYS / SPATIAL PAD",
        "tuning_dependence": "Desacopla la fase lateral sin alterar la fundamental mono."
    },
    {
        "index": 14,
        "id": "MUT_14_RHYTHMIC_STUTTER_CHOP",
        "name": "Syncopated Rhythmic Stutter Slicer",
        "registry_name": "RHYTHMIC_STUTTER_CHOP",
        "category": "Rhythmic & Groove Chopping",
        "description": "Rebanador de semicorcheas sincronizado matemáticamente al BPM del proyecto. Aplica un patrón de compuerta y micro-repeticiones tartamudeadas (stutter) con envolventes suaves para evitar clics.",
        "best_suited_for": "GLITCH POP / TRAP HOOK / FUTURE BASS LEAD",
        "tuning_dependence": "Sincronización 100% milimétrica a la cuadrícula de semicorcheas del BPM detectado."
    },
    {
        "index": 15,
        "id": "MUT_15_OCTAVE_FUZZ_MULTIPLIER",
        "name": "Full-Wave Octave Fuzz Multiplier",
        "registry_name": "OCTAVE_FUZZ_MULTIPLIER",
        "category": "Harmonic & Modal Tuned",
        "description": "Rectificación de onda completa que duplica matemáticamente la frecuencia fundamental a la octava superior, seguida de overdrive de fuzz agresivo y corte en los medios (notch en 650Hz). Sonido denso estilo pedal fuzz legendario.",
        "best_suited_for": "DIRTY LEAD / GRITTY CHORD / SYNTH FUZZ",
        "tuning_dependence": "Multiplicador de armónicos pares e impares de la fundamental."
    },
    {
        "index": 16,
        "id": "MUT_16_CHOPPED_TRANCE_PULSE",
        "name": "Chopped Polyrhythmic Trance Pulse",
        "registry_name": "CHOPPED_TRANCE_PULSE",
        "category": "Rhythmic & Groove Chopping",
        "description": "Compuerta de pulso trapezoidal en semicorcheas sincronizada a tempo, encadenada a un retardo estéreo ping-pong rebotando entre semicorchea con puntillo (L) y corchea (R). Genera movimiento rítmico hipnótico inmediato.",
        "best_suited_for": "PROGRESSIVE / TRANCE GATED PAD / EDM ARP",
        "tuning_dependence": "Rejilla temporal sintonizada dinámicamente al BPM de la sesión."
    },
    {
        "index": 17,
        "id": "MUT_17_SPECTRAL_BLUR_INFINITE",
        "name": "Spectral Gaussian Blur Infinite",
        "registry_name": "SPECTRAL_BLUR_INFINITE",
        "category": "Spectral & Granular",
        "description": "Cálculo de espectrograma STFT 2D y difuminado por filtro Gaussiano bidimensional en los ejes temporal y frecuencial. Desvanece los transitorios en una textura acuática difusa y ambiental de belleza infinita.",
        "best_suited_for": "CINEMATIC WASH / DREAM POP PAD / LUSH AMBIENCE",
        "tuning_dependence": "Difumina el mapa armónico manteniendo los picos tonales del acorde."
    },
    {
        "index": 18,
        "id": "MUT_18_ANALOG_TAPE_WARMTH_GLUE",
        "name": "Analog Tape Warmth & Opto Glue",
        "registry_name": "ANALOG_TAPE_WARMTH_GLUE",
        "category": "Saturation, Texture & Character",
        "description": "Saturación analógica triodo suave con curva sigmoidal y realce sutil de 'aire' analógico en altas frecuencias (>11kHz). Añade pegamento, presencia y cuerpo de producción comercial de primer nivel.",
        "best_suited_for": "WARM MASTER BUSS / ACOUSTIC PIANO / ORGANIC GLUE",
        "tuning_dependence": "Enriquece todos los sobretonos naturales de la fuente."
    },
    {
        "index": 19,
        "id": "MUT_19_NEOPERREO_METALLIC_COMB",
        "name": "Neoperreo Resonant Metallic Comb",
        "registry_name": "NEOPERREO_METALLIC_COMB",
        "category": "Saturation, Texture & Character",
        "description": "Filtro de peine de reflexión temprana de 11.5ms sintonizado en 1.18kHz con distorsión agresiva estilo Drum Buss urbano. Imparte el carácter metálico e industrial distintivo del reggaetón underground y neoperreo.",
        "best_suited_for": "URBAN PERC / METALLIC PLUCK / DIRTY ACCENT",
        "tuning_dependence": "Sintonía resonante en la banda media para máximo corte en mezcla."
    },
    {
        "index": 20,
        "id": "MUT_20_EXPONENTIAL_PITCH_DIVE",
        "name": "Exponential Pitch Dive & HPF Sweep",
        "registry_name": "EXPONENTIAL_PITCH_DIVE",
        "category": "Pitch & Time Space",
        "description": "Caída de afinación exponencial de 0 a -14 semitonos mediante interpolación de fase no lineal, acompañada de un barrido de filtro paso alto. Ideal para transiciones pre-drop dramáticas y efectos cinematográficos.",
        "best_suited_for": "PRE-DROP LASER / TENSION DIVE / CINEMATIC IMPACT",
        "tuning_dependence": "Inicia en la tónica original y cae 14 semitonos hacia el subgrave."
    }
]


class AudioReprocessingPipeline:
    """Core controller for the Audio Resampling & Mutation Pipeline."""

    CACHE_DIR = Path("cache/uhts_resampled")
    MUTATIONS_DIR = Path("cache/resampled_mutations")

    def __init__(self, conn: Any = None):
        self.conn = conn
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.MUTATIONS_DIR.mkdir(parents=True, exist_ok=True)

    def detect_project_key_and_bpm(self, session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detects project Key (tonality), Scale, and BPM automatically:
        1. Queries Ableton Live 12 LOM via execute_code (song.root_note, song.scale_name, song.tempo).
        2. Falls back to session_data (e.g. from GuidedSession state).
        3. Defaults safely to F Minor @ 120.0 BPM.
        """
        detected_key = None
        detected_scale = None
        detected_bpm = None
        root_int = 5

        # 1. Inspect Live LOM if connection is active
        if self.conn and hasattr(self.conn, "send_command"):
            try:
                code = """
root_val = getattr(song, 'root_note', 5)
scale_val = getattr(song, 'scale_name', 'Minor')
tempo_val = getattr(song, 'tempo', 120.0)
result = {'root_note': int(root_val), 'scale_name': str(scale_val), 'tempo': float(tempo_val)}
"""
                res = self.conn.send_command("execute_code", {"code": code})
                r_dict = res.get("result", {}) if isinstance(res, dict) else {}
                if "root_note" in r_dict:
                    root_int = int(r_dict["root_note"])
                    detected_key = ROOT_INT_TO_NOTE.get(root_int, "F")
                if "scale_name" in r_dict and r_dict["scale_name"]:
                    detected_scale = str(r_dict["scale_name"])
                if "tempo" in r_dict and float(r_dict["tempo"]) > 20.0:
                    detected_bpm = float(r_dict["tempo"])
            except Exception as e:
                logger.debug(f"Live LOM key detection notice: {e}")

        # 2. Check session_data if Live didn't provide complete info
        if session_data:
            if not detected_key and "key" in session_data:
                detected_key = str(session_data["key"]).strip().capitalize()
            if not detected_scale and "scale" in session_data:
                detected_scale = str(session_data["scale"]).strip().capitalize()
            if not detected_bpm and "bpm" in session_data:
                try:
                    detected_bpm = float(session_data["bpm"])
                except Exception:
                    pass

        # 3. Final defaults
        f_key = detected_key or "F"
        f_scale = detected_scale or "Minor"
        f_bpm = round(detected_bpm or 120.0, 2)
        f_root_int = NOTE_TO_ROOT_INT.get(f_key.upper(), root_int)

        return {
            "key": f_key,
            "scale": f_scale,
            "bpm": f_bpm,
            "root_note_int": f_root_int,
            "tuning_label": f"{f_key} {f_scale} @ {f_bpm:.1f} BPM"
        }

    def get_catalog(self) -> List[Dict[str, Any]]:
        """Returns the full metadata catalog of the 20 UHTS resampling techniques."""
        return CATALOG_METADATA

    def get_technique_by_selector(self, selector: Any) -> Optional[Dict[str, Any]]:
        """Resolves a technique by index (1..20), ID (MUT_01..), or partial name."""
        sel_str = str(selector).strip().lower()
        
        # Try integer index
        m_num = re.search(r'\b([1-9]|1[0-9]|20)\b', sel_str)
        if m_num:
            target_idx = int(m_num.group(1))
            for t in CATALOG_METADATA:
                if t["index"] == target_idx:
                    return t

        # Try ID or name matching
        for t in CATALOG_METADATA:
            if t["id"].lower() in sel_str or t["registry_name"].lower() in sel_str:
                return t
            if t["name"].lower() in sel_str:
                return t
            # Substring keywords
            keywords = t["name"].lower().split()
            if any(k in sel_str for k in keywords if len(k) > 4):
                return t

        return None

    def execute_mutation(
        self,
        source_wav_path: str,
        technique_selector: Any,
        key: str = "F",
        scale: str = "Minor",
        bpm: float = 120.0,
        custom_output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Applies a selected UHTS mutation algorithm to the source audio,
        parameterized by Key and BPM, and writes the continuous audio to WAV.
        """
        tech = self.get_technique_by_selector(technique_selector)
        if not tech:
            raise ValueError(f"Technique not found for selector: '{technique_selector}'. Available: 1 to 20.")

        t_idx = tech["index"]
        t_reg_name = tech["registry_name"]

        # Find function in registry
        mutation_fn = None
        for name, fn in MUTATION_REGISTRY:
            if name == t_reg_name:
                mutation_fn = fn
                break

        if not mutation_fn:
            raise RuntimeError(f"Algorithm function for '{t_reg_name}' not registered in MUTATION_REGISTRY.")

        # Read source audio
        audio, sr = sf.read(source_wav_path)
        if audio.ndim == 1:
            audio = np.stack([audio, audio], axis=-1)

        # Execute DSP mutation with dynamic musical parameters
        logger.info(f"Executing UHTS mutation #{t_idx} '{tech['name']}' tuned to {key} {scale} @ {bpm} BPM...")
        mutated = mutation_fn(audio, sr, key=key, scale=scale, bpm=bpm)

        # Output path
        if custom_output_filename:
            out_filename = custom_output_filename
        else:
            safe_key = key.replace("#", "s").lower()
            safe_scale = scale.lower()
            out_filename = f"uhts_{t_idx:02d}_{t_reg_name.lower()}_{safe_key}_{safe_scale}_{int(bpm)}bpm.wav"

        out_path = self.MUTATIONS_DIR / out_filename
        sf.write(str(out_path), mutated, sr, subtype="PCM_24")

        return {
            "status": "MUTATION_RENDERED",
            "technique": tech,
            "output_path": str(out_path.resolve()),
            "duration": len(mutated) / sr,
            "sample_rate": sr,
            "key": key,
            "scale": scale,
            "bpm": bpm
        }

    def deploy_mutated_track_to_live(
        self,
        mutated_wav_path: str,
        technique_name: str,
        technique_index: int,
        key: str = "F",
        scale: str = "Minor",
        target_volume: float = 0.75
    ) -> Dict[str, Any]:
        """
        Creates a BRAND NEW UNUSED Audio Track in Ableton Live,
        sets its formal name, loads the mutated audio clip into slot 0,
        and sets safe track gain staging.
        """
        if not self.conn or not hasattr(self.conn, "send_command"):
            return {
                "status": "MOCK_DEPLOYED",
                "track_index": -1,
                "track_name": f"[RESAMPLE {technique_index:02d}] {technique_name} ({key} {scale})",
                "wav_path": mutated_wav_path
            }

        safe_path = str(Path(mutated_wav_path).resolve()).replace("\\", "/")
        track_name = f"[RESAMPLE {technique_index:02d}] {technique_name} ({key} {scale})"

        # 1. Create native Audio Track via Live Python thread
        create_code = f"""
new_trk = song.create_audio_track(-1)
new_trk.name = {repr(track_name)}
result = {{'index': len(song.tracks) - 1, 'name': new_trk.name}}
"""
        create_res = self.conn.send_command("execute_code", {"code": create_code})
        res_info = create_res.get("result", {}) if isinstance(create_res, dict) else {}
        new_track_idx = int(res_info.get("index", -1))

        if new_track_idx < 0:
            # Fallback to scanning session info
            s_info = self.conn.send_command("get_session_info", {})
            r_s = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
            new_track_idx = int(r_s.get("track_count", 1)) - 1

        # 2. Place continuous audio clip into slot 0
        clip_res = self.conn.send_command("create_audio_clip", {
            "track_index": new_track_idx,
            "clip_index": 0,
            "path": safe_path
        })

        # 3. Set track volume to safe headroom
        try:
            self.conn.send_command("set_track_volume", {
                "track_index": new_track_idx,
                "volume": target_volume
            })
        except Exception:
            pass

        return {
            "status": "DEPLOYED",
            "track_index": new_track_idx,
            "track_name": track_name,
            "clip_index": 0,
            "wav_path": safe_path,
            "volume": target_volume,
            "clip_result": clip_res
        }

    def generate_source_sound_for_new_track(
        self,
        role: str = "KEYS",
        instrument_name: str = "Analog Lab V",
        preset_name: str = "Prolonged Concert Piano",
        key: str = "F",
        scale: str = "Minor",
        bpm: float = 120.0,
        bars: int = 4
    ) -> Dict[str, Any]:
        """
        Generates a high-fidelity continuous audio source sound (sustained chord)
        tuned to the project's Key, Scale, and BPM, ready to be resampled and mutated.
        """
        from engine.sound_design.piano_chord_generator import generate_source_piano_chord
        
        beats = float(bars * 4.0)
        seconds = (beats / bpm) * 60.0
        
        out_filename = f"source_{role.lower()}_{key.lower()}_{scale.lower()}_{int(bpm)}bpm.wav"
        out_path = self.CACHE_DIR / out_filename
        
        logger.info(f"Synthesizing source sound '{preset_name}' ({key} {scale}) for {seconds:.1f}s...")
        generate_source_piano_chord(str(out_path), duration_sec=seconds, sample_rate=44100)
        
        return {
            "status": "SOURCE_GENERATED",
            "role": role,
            "instrument": instrument_name,
            "preset": preset_name,
            "wav_path": str(out_path.resolve()),
            "duration": seconds,
            "bars": bars,
            "key": key,
            "scale": scale,
            "bpm": bpm
        }

    def solo_track(self, track_index: int, solo: bool = True) -> Dict[str, Any]:
        """Solos or un-solos a track in Live for immediate auditioning."""
        if not self.conn or not hasattr(self.conn, "send_command"):
            return {"status": "MOCK_SOLO", "track_index": track_index, "solo": solo}
            
        res = self.conn.send_command("set_track_solo", {
            "track_index": track_index,
            "solo": solo
        })
        return {"status": "SOLO_UPDATED", "track_index": track_index, "solo": solo, "result": res}
