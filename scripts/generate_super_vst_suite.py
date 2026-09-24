r"""
Super VST Sound Design Suite Generator:
1. Generates 5 studio-grade Surge XT Synthesizer patches (.surgepatch)
2. Generates 5 studio-grade Surge XT FX Multi-Slot Chains (.srgfxchain)
3. Safely extracts Decent Sampler ZIP libraries in D:\Documentos\Librerias FL Studio\Decent Sampler
4. Audits all Decent Sampler libraries and builds an index
5. Compiles a custom Decent Sampler instrument template with UI macro knobs
"""

import os
import sys
import zipfile
from pathlib import Path

# AbletonEngine imports
from engine.sound_design.surge_xt_synth.patch_factory import SurgeSynthPatchFactory
from engine.sound_design.surge_xt_synth.serializer import SurgeSynthSerializer
from engine.sound_design.surge_xt_synth.schema import SurgeOscillatorType, SurgeFilterType
from engine.sound_design.surge_xt_synth.model import (
    SurgeSynthPatchModel, SurgeSynthOscillatorModel, SurgeSynthFilterModel, SurgeSynthEnvelopeModel
)

from engine.sound_design.surge_xt_fx.rack_factory import SurgeFXRackFactory
from engine.sound_design.surge_xt_fx.serializer import SurgeFXSerializer
from engine.sound_design.surge_xt_fx.schema import FXChain, FXType
from engine.sound_design.surge_xt_fx.builder import SurgeFXSlotBuilder, SurgeFXRackBuilder

from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
from engine.sound_design.decent_sampler.builder import DecentSamplerBuilder
from engine.sound_design.decent_sampler.serializer import DSPresetSerializer

def generate_surge_synth_patches():
    print("\n--- [1/4] Generando Patches de Sintetizador Surge XT (.surgepatch) ---")
    
    docs_dir = Path.home() / "Documents" / "Surge XT" / "Patches" / "AbletonEngine"
    local_dir = Path("state/presets/surge_xt_synth")
    docs_dir.mkdir(parents=True, exist_ok=True)
    local_dir.mkdir(parents=True, exist_ok=True)

    patches = [
        # 1. Bass Reese
        ("Bass_Reese_Analog.surgepatch", SurgeSynthPatchFactory.build_bass_reese_patch(patch_name="Bass_Reese_Analog")),
        
        # 2. Lead Supersaw
        ("Lead_Supersaw_Modular.surgepatch", SurgeSynthPatchFactory.build_lead_supersaw_patch(patch_name="Lead_Supersaw_Modular")),
        
        # 3. Keys FM Pluck
        ("Keys_FM_Pluck.surgepatch", SurgeSynthPatchFactory.build_pluck_fm_patch(patch_name="Keys_FM_Pluck")),
        
        # 4. Pad Lush String
        ("Pad_Lush_String.surgepatch", SurgeSynthPatchFactory.build_pad_lush_patch(patch_name="Pad_Lush_String")),
        
        # 5. Bass 808 Sub
        ("Bass_808_Sub.surgepatch", SurgeSynthPatchFactory.build_808_sub_patch(patch_name="Bass_808_Sub")),
    ]

    for filename, patch in patches:
        SurgeSynthSerializer.save_patch(patch, docs_dir / filename)
        SurgeSynthSerializer.save_patch(patch, local_dir / filename)
        print(f"  [+] Generado: {filename}")
        print(f"      -> {docs_dir / filename}")

def generate_surge_fx_chains():
    print("\n--- [2/4] Generando Cadenas Multislot de Efectos Surge XT (.srgfxchain) ---")
    
    docs_dir = Path.home() / "Documents" / "Surge XT" / "FX Chains" / "AbletonEngine"
    local_dir = Path("state/presets/surge_xt_fx")
    docs_dir.mkdir(parents=True, exist_ok=True)
    local_dir.mkdir(parents=True, exist_ok=True)

    # 5 Racks
    racks = [
        ("Drum_Glue_Bus", SurgeFXRackFactory.build_drum_glue_rack(rack_name="Drum_Glue_Bus")),
        ("Bass_Power_Rack", SurgeFXRackFactory.build_bass_power_rack(rack_name="Bass_Power_Rack")),
        ("Keys_Vintage_Ensemble", SurgeFXRackFactory.build_keys_vintage_rack(rack_name="Keys_Vintage_Ensemble")),
        ("Ambient_Pad_Nimbus", SurgeFXRackFactory.build_ambient_pad_rack(rack_name="Ambient_Pad_Nimbus")),
        ("Lead_Overdrive_Chain", SurgeFXRackFactory.build_lead_overdrive_rack(rack_name="Lead_Overdrive_Chain")),
    ]

    for name, rack in racks:
        slots = rack.get_chain_slots(FXChain.SCENE_A)
        p1 = docs_dir / f"{name}.srgfxchain"
        p2 = local_dir / f"{name}.srgfxchain"
        SurgeFXSerializer.save_chain_fx_file(name, slots, p1)
        SurgeFXSerializer.save_chain_fx_file(name, slots, p2)
        print(f"  [+] Generado Rack FX: {name}.srgfxchain")
        print(f"      -> {p1}")

def extract_and_audit_decent_sampler_libraries():
    print("\n--- [3/4] Descomprimiendo y Auditando Librerias de Decent Sampler ---")
    
    ds_root = DecentSamplerLibraryManager.get_library_root()
    print(f"  Ruta raiz: {ds_root}")

    # Find zip files
    zip_files = list(ds_root.glob("*.zip"))
    print(f"  Archivos ZIP detectados para extraccion: {len(zip_files)}")

    for zf in zip_files:
        stem = zf.stem
        # Target folder
        out_folder = ds_root / stem
        if not out_folder.exists() or len(list(out_folder.iterdir())) == 0:
            print(f"  [Extrayendo] {zf.name} ...")
            try:
                with zipfile.ZipFile(zf, 'r') as zip_ref:
                    zip_ref.extractall(out_folder)
                print(f"    -> Extraido en: {out_folder.name}")
            except Exception as e:
                print(f"    [!] Error al extraer {zf.name}: {e}")
        else:
            print(f"  [OK] Ya extraido previamente: {out_folder.name}")

    # Run pre-flight audit
    print("\n  Auditando todas las librerias disponibles en Decent Sampler...")
    valid_libs = DecentSamplerLibraryManager.scan_libraries(require_valid=True)
    print(f"  Total de librerias de Decent Sampler CERTIFICADAS Y VALIDAS: {len(valid_libs)}")
    for l in valid_libs:
        print(f"    * {l.name:<35} | Rol: {l.role_hint:<7} | Muestras: {l.sample_count:>3} | Preset: {l.preset_path.name if l.preset_path else 'Muestras'}")

def compile_custom_decent_sampler_instrument():
    print("\n--- [4/4] Compilando Instrumento Custom en Decent Sampler (.dspreset) ---")
    
    ds_root = DecentSamplerLibraryManager.get_library_root()
    dest_dir = ds_root / "Custom_Studio_Synthesizer"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    preset_file = dest_dir / "Studio_Synthesizer.dspreset"
    
    # Ensure sample audio file exists
    samples_dir = dest_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    sample_file = samples_dir / "sine_c4.wav"
    if not sample_file.exists():
        import math, wave, struct
        sr = 44100
        dur = 4.0
        freq = 261.625565
        n = int(sr * dur)
        with wave.open(str(sample_file), 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            frames = bytearray()
            for i in range(n):
                t = i / sr
                val = 0.85 * math.sin(2 * math.pi * freq * t) + 0.10 * math.sin(4 * math.pi * freq * t) + 0.05 * math.sin(6 * math.pi * freq * t)
                if i > n - 2000:
                    val *= (n - i) / 2000.0
                s = int(max(min(val, 1.0), -1.0) * 32767)
                frames.extend(struct.pack('<hh', s, s))
            wf.writeframes(frames)
        print(f"  [+] Generado sample C4: {sample_file.name}")

    # Build and save a clean DSPreset with UI macro knobs (Cutoff, Reverb, ADSR)
    builder = (
        DecentSamplerBuilder(name="Studio Synthesizer")
        .set_envelope(attack=0.02, decay=0.30, sustain=0.75, release=0.40)
        .add_sample(path="samples/sine_c4.wav", root_note=60, lo_note=0, hi_note=127)
        .add_effect(effect_type="lowpass", cutoff=3500.0, resonance=1.2)
        .add_effect(effect_type="reverb", wet=0.30, room_size=0.65)
        .add_macro_knob(label="Filter Cutoff", parameter="FX_FILTER_CUTOFF", min_value=50.0, max_value=18000.0, default_value=3500.0)
        .add_macro_knob(label="Reverb Wet", parameter="FX_REVERB_WET", min_value=0.0, max_value=1.0, default_value=0.30)
    )

    out_path = builder.save(str(preset_file))
    print(f"  [+] Compilado exitosamente: {preset_file.name}")
    print(f"      -> {out_path}")

if __name__ == "__main__":
    generate_surge_synth_patches()
    generate_surge_fx_chains()
    extract_and_audit_decent_sampler_libraries()
    compile_custom_decent_sampler_instrument()
    print("\n========================================================")
    print("[EXITO] Suite de diseno sonoro completada y guardada en disco.")
