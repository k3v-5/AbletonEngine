| Subsystem / Operation | Baseline (s) | Optimized (s) | Delta (s) | Speedup (%) | Factor |
|:---|---:|---:|---:|---:|---:|
| **1. Module Import & Startup Overhead** | | | | | |
| Import server | 9.2826s | 1.7580s | -7.5246s | +81.1% | 5.28x |
| Import engine.sound.engine | 0.4149s | 1.0853s | +0.6704s | -161.6% | 0.38x |
| Import engine.production.copilot.guided_session | 0.5580s | 1.2087s | +0.6507s | -116.6% | 0.46x |
| Import engine.production.doctor.session_doctor | 0.4340s | 1.0685s | +0.6345s | -146.2% | 0.41x |
| Import engine.mix.loudness_analyzer | 0.4028s | 1.0380s | +0.6352s | -157.7% | 0.39x |
| Total Cold Imports | 11.0924s | 6.1586s | -4.9338s | +44.5% | 1.80x |
| **2. Scanner & Library Lookups** | | | | | |
| InstalledPluginScanner.scan | 0.0002s | 0.0002s | +0.0000s | -20.9% | 0.83x |
| DecentSamplerLibraryManager.scan_libraries | 0.0352s | 0.0315s | -0.0037s | +10.5% | 1.12x |
| DecentSamplerLibraryManager.get_libraries_for_role (6 roles) | 0.1948s | 0.0035s | -0.1912s | +98.2% | 55.11x |
| AuthenticSampleDrumRackEngine.build_sample_index | 0.0008s | 0.0006s | -0.0001s | +18.5% | 1.23x |
| Total Scanner Operations | 0.2309s | 0.0358s | -0.1951s | +84.5% | 6.44x |
| **3. Core Guided Session Execution** | | | | | |
| Phase 1: Scaffolding | 0.1551s | 0.0064s | -0.1487s | +95.9% | 24.23x |
| Phase 2: Sections | 0.0346s | 0.0040s | -0.0306s | +88.4% | 8.59x |
| Phase 3: Instruments (5 tracks) | 0.2892s | 0.0111s | -0.2780s | +96.2% | 26.00x |
| Phase 4: Synthesis Sculpting (5 tracks) | 0.0324s | 0.0332s | +0.0008s | -2.5% | 0.98x |
| Phase 5: Insert Effects Chains | 0.8827s | 0.8813s | -0.0014s | +0.2% | 1.00x |
| Phase 6: Composition MIDI Generation | 0.0178s | 0.0168s | -0.0010s | +5.6% | 1.06x |
| Phase 7: Dynamic Automation Injection | 0.0103s | 0.0094s | -0.0009s | +9.1% | 1.10x |
| Phase 8: Vocal Ducking Calibration | 0.0096s | 0.0075s | -0.0020s | +21.1% | 1.27x |
| Phase 9: Mix, Master & LUFS Gatekeeper | 3.6375s | 0.1129s | -3.5246s | +96.9% | 32.21x |
| Total Guided Session Walkthrough | 5.0693s | 1.0828s | -3.9865s | +78.6% | 4.68x |
| **4. Session Doctor Execution** | | | | | |
| CopilotSessionDoctor Diagnostic Scan | 0.0016s | 0.0019s | +0.0003s | -16.8% | 0.86x |
| CopilotSessionDoctor Triage Step | 0.0008s | 0.0009s | +0.0001s | -11.3% | 0.90x |
| Total Doctor Operations | 0.0024s | 0.0027s | +0.0004s | -15.0% | 0.87x |
| **5. Audio DSP & LUFS Validation** | | | | | |
| LoudnessAnalyzer._apply_k_weighting (5s audio) | 0.7261s | 0.0076s | -0.7186s | +99.0% | 96.06x |
| LoudnessAnalyzer.calculate_true_peak (4x oversample) | 0.0352s | 0.0369s | +0.0017s | -4.9% | 0.95x |
| LoudnessAnalyzer.calculate_lufs_with_blocks | 0.7307s | 0.0072s | -0.7235s | +99.0% | 102.05x |
| Total Audio DSP Pipeline (5s audio) | 1.4920s | 0.0516s | -1.4403s | +96.5% | 28.90x |
| **6. Pytest Test Suite Runtimes** | | | | | |
| pytest tests/test_lufs_validation_gate.py | 13.0878s | 2.7292s | -10.3586s | +79.1% | 4.80x |
| pytest tests/test_session_doctor.py | 10.5504s | 3.0218s | -7.5286s | +71.4% | 3.49x |
| pytest tests/governance/ | 14.0388s | 5.6311s | -8.4077s | +59.9% | 2.49x |
| pytest tests/test_guided_session.py | 76.4194s | 22.7004s | -53.7190s | +70.3% | 3.37x |
| Total Pytest Runtime | 114.0965s | 34.0826s | -80.0139s | +70.1% | 3.35x |