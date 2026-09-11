# Project Architecture

```mermaid
graph TD;
    engine_adapters_ableton_adapter:::engine
    engine_adapters_base:::engine
    engine_adapters_mock_adapter:::engine
    engine_arrangement_arrangement_composer:::engine
    engine_arrangement_automation_clip_suggester:::engine
    engine_arrangement_automation_live_automation:::engine
    engine_arrangement_automation_recorder:::engine
    engine_arrangement_automation_weaver:::engine
    engine_arrangement_blueprints_song_arranger:::engine
    engine_arrangement_compiler:::engine
    engine_arrangement_density:::engine
    engine_arrangement_drops_engine:::engine
    engine_arrangement_energy_curve:::engine
    engine_arrangement_energy_dimensions:::engine
    engine_arrangement_fx_ear_candy:::engine
    engine_arrangement_fx_ear_candy_transitions:::engine
    engine_arrangement_generator:::engine
    engine_arrangement_impacts_downlifters:::engine
    engine_arrangement_linter_comparison:::engine
    engine_arrangement_linter_linter:::engine
    engine_arrangement_locking:::engine
    engine_arrangement_models_section:::engine
    engine_arrangement_models_song:::engine
    engine_arrangement_narrative_arc:::engine
    engine_arrangement_roles_matrix:::engine
    engine_arrangement_roles_orchestrator:::engine
    engine_arrangement_scoring:::engine
    engine_arrangement_structure_beat_switch:::engine
    engine_arrangement_templates_genres:::engine
    engine_arrangement_templates_structures:::engine
    engine_arrangement_transitions_automation:::engine
    engine_arrangement_transitions_engine:::engine
    engine_arrangement_transitions_impacts:::engine
    engine_arrangement_transitions_models:::engine
    engine_arrangement_transitions_pre_drop:::engine
    engine_arrangement_transitions_risers:::engine
    engine_arrangement_variation_motifs:::engine
    engine_arrangement_variation_planner:::engine
    engine_audio_chopper_transient:::engine
    engine_audio_deconstruction_expressive_transcriber:::engine
    engine_audio_deconstruction_models:::engine
    engine_audio_deconstruction_neural_separator:::engine
    engine_audio_deconstruction_reconstructor:::engine
    engine_audio_deconstruction_separator:::engine
    engine_audio_deconstruction_transcriber:::engine
    engine_audio_live_listener:::engine
    engine_audio_sample_generator:::engine
    engine_audio_semantic_sample_matcher:::engine
    engine_audio_stem_audit:::engine
    engine_audio_stem_bouncer:::engine
    engine_config:::engine
    engine_creative_dna_engine:::engine
    engine_creative_models:::engine
    engine_errors:::engine
    engine_events_event_logger:::engine
    engine_forensics_analyzer:::engine
    engine_forensics_anomalies:::engine
    engine_forensics_baseline:::engine
    engine_forensics_causality:::engine
    engine_forensics_clipping:::engine
    engine_forensics_config:::engine
    engine_forensics_correlation:::engine
    engine_forensics_exceptions:::engine
    engine_forensics_masking:::engine
    engine_forensics_models:::engine
    engine_forensics_report:::engine
    engine_forensics_serializer:::engine
    engine_forensics_spectral:::engine
    engine_forensics_stft:::engine
    engine_forensics_temporal:::engine
    engine_fx_device_parameter_supervisor:::engine
    engine_fx_track_fx_rack:::engine
    engine_indexer_fileinfo:::engine
    engine_indexer_keywords:::engine
    engine_indexer_manifest:::engine
    engine_indexer_parser:::engine
    engine_indexer_paths:::engine
    engine_indexer_storage:::engine
    engine_indexer_walker:::engine
    engine_instruments_browser_catalog:::engine
    engine_instruments_drum_map:::engine
    engine_instruments_drum_rack_guard:::engine
    engine_instruments_execution_planner:::engine
    engine_instruments_installed_scanner:::engine
    engine_instruments_library_crawler:::engine
    engine_instruments_library_preset_catalog:::engine
    engine_instruments_library_resolver:::engine
    engine_instruments_library_search:::engine
    engine_instruments_models:::engine
    engine_instruments_plugins_models:::engine
    engine_instruments_plugins_normalizer:::engine
    engine_instruments_plugins_registry:::engine
    engine_instruments_presets_adapters_arturia_db:::engine
    engine_instruments_presets_adapters_fabfilter_tree:::engine
    engine_instruments_presets_adapters_native_adapter:::engine
    engine_instruments_presets_adapters_serum_adapter:::engine
    engine_instruments_presets_adapters_valhalla_adapter:::engine
    engine_instruments_presets_adapters_vital_adapter:::engine
    engine_instruments_presets_models:::engine
    engine_instruments_presets_patch_decision:::engine
    engine_instruments_presets_search:::engine
    engine_instruments_presets_universal_indexer:::engine
    engine_instruments_profiles_drum_kits:::engine
    engine_instruments_profiles_sound_profiles:::engine
    engine_instruments_rack_builder:::engine
    engine_instruments_rack_inspector:::engine
    engine_instruments_rack_verifier:::engine
    engine_instruments_roles:::engine
    engine_instruments_vst_guard:::engine
    engine_knowledge_arrangement_song_structures:::engine
    engine_knowledge_composition_basslines:::engine
    engine_knowledge_composition_chords:::engine
    engine_knowledge_composition_drum_patterns:::engine
    engine_knowledge_composition_scales:::engine
    engine_knowledge_constants:::engine
    engine_knowledge_plugins_autotune:::engine
    engine_knowledge_plugins_cymatics:::engine
    engine_knowledge_plugins_fabfilter:::engine
    engine_knowledge_plugins_mixing_advanced:::engine
    engine_knowledge_plugins_ozone12:::engine
    engine_knowledge_plugins_plugin_chains:::engine
    engine_knowledge_plugins_rx11:::engine
    engine_knowledge_plugins_serum2:::engine
    engine_knowledge_plugins_vocal_chains:::engine
    engine_knowledge_producers_producers:::engine
    engine_knowledge_sampling_sampling:::engine
    engine_mastering_compressor:::engine
    engine_mastering_dynamics:::engine
    engine_mastering_eq:::engine
    engine_mastering_export_manager:::engine
    engine_mastering_guided_mastering:::engine
    engine_mastering_limiter:::engine
    engine_mastering_live_master_chain:::engine
    engine_mastering_loudness_target:::engine
    engine_mastering_mastering_analyzer:::engine
    engine_mastering_mastering_chain:::engine
    engine_mastering_mastering_engine:::engine
    engine_mastering_models:::engine
    engine_mastering_optimizer:::engine
    engine_mastering_quality_control:::engine
    engine_mastering_reference_match:::engine
    engine_mastering_release_package:::engine
    engine_mastering_reports:::engine
    engine_mastering_rollback:::engine
    engine_mastering_saturation:::engine
    engine_mastering_snapshot:::engine
    engine_mastering_stereo:::engine
    engine_mastering_tonal_balance:::engine
    engine_mastering_translation_test:::engine
    engine_mastering_true_peak:::engine
    engine_memory_user_learning:::engine
    engine_midi_program_change:::engine
    engine_mix_audio_capture:::engine
    engine_mix_balance_analyzer:::engine
    engine_mix_bridge:::engine
    engine_mix_channel_strip:::engine
    engine_mix_confidence:::engine
    engine_mix_conflict_graph:::engine
    engine_mix_correction_engine:::engine
    engine_mix_diagnostic_engine:::engine
    engine_mix_dynamics_analyzer:::engine
    engine_mix_eq_dynamic_eq:::engine
    engine_mix_eq_resonance:::engine
    engine_mix_fader_rider:::engine
    engine_mix_feature_extractor:::engine
    engine_mix_frequency_analyzer:::engine
    engine_mix_frequency_slotting:::engine
    engine_mix_gain_staging_auto_stager:::engine
    engine_mix_loudness_analyzer:::engine
    engine_mix_loudness_standards:::engine
    engine_mix_lufs_validation_gate:::engine
    engine_mix_masking_detector:::engine
    engine_mix_mix_linter:::engine
    engine_mix_models:::engine
    engine_mix_multitrack_sidechain:::engine
    engine_mix_phase_alignment:::engine
    engine_mix_psychoacoustic_masking:::engine
    engine_mix_reference_engine:::engine
    engine_mix_render_manager:::engine
    engine_mix_reports:::engine
    engine_mix_sidechain:::engine
    engine_mix_sidechain_manager:::engine
    engine_mix_spatial_depth:::engine
    engine_mix_static_auditor:::engine
    engine_mix_stereo_analyzer:::engine
    engine_mix_transient_analyzer:::engine
    engine_mix_vocal_analyzer:::engine
    engine_models_ids:::engine
    engine_models_roles:::engine
    engine_models_session:::engine
    engine_models_transactions:::engine
    engine_music_analyzer:::engine
    engine_music_bass_glide:::engine
    engine_music_bass_intelligent_808:::engine
    engine_music_drums_evolver:::engine
    engine_music_drums_genre_grooves:::engine
    engine_music_drums_ghost_notes:::engine
    engine_music_drums_multitrack:::engine
    engine_music_expression_mpe:::engine
    engine_music_generators:::engine
    engine_music_groove_humanizer:::engine
    engine_music_groove_pocket:::engine
    engine_music_groove_pool:::engine
    engine_music_groove_profiles:::engine
    engine_music_harmony_chords:::engine
    engine_music_harmony_full_song:::engine
    engine_music_harmony_generator:::engine
    engine_music_harmony_reharmonizer:::engine
    engine_music_harmony_roman:::engine
    engine_music_harmony_strum:::engine
    engine_music_humanizer_engine:::engine
    engine_music_intent:::engine
    engine_music_melody_counterpoint:::engine
    engine_music_melody_topline:::engine
    engine_music_melody_vocal_hook:::engine
    engine_music_midi_compiler:::engine
    engine_music_models:::engine
    engine_music_motifs_memory:::engine
    engine_music_motifs_motif:::engine
    engine_music_motifs_transformations:::engine
    engine_music_mutation_engine:::engine
    engine_music_rhythm_generator:::engine
    engine_music_rhythm_grid:::engine
    engine_music_rhythm_templates:::engine
    engine_music_song_state:::engine
    engine_music_theory_notes:::engine
    engine_music_theory_scales:::engine
    engine_music_validation_constraints:::engine
    engine_music_validation_repair:::engine
    engine_music_variation_engine:::engine
    engine_music_variation_phrase_evolver:::engine
    engine_music_voicing_profiles:::engine
    engine_music_voicing_voice_leading:::engine
    engine_persistence_storage:::engine
    engine_presets_analog_lab_ui_automator:::engine
    engine_presets_catalog:::engine
    engine_production_boundary:::engine
    engine_production_completeness:::engine
    engine_production_context:::engine
    engine_production_copilot_guided_session:::engine
    engine_production_copilot_models:::engine
    engine_production_copilot_recipes:::engine
    engine_production_copilot_role_orchestrator:::engine
    engine_production_copilot_stepper:::engine
    engine_production_exceptions:::engine
    engine_production_executor:::engine
    engine_production_full_song_producer:::engine
    engine_production_graph:::engine
    engine_production_memory:::engine
    engine_production_models:::engine
    engine_production_planner:::engine
    engine_production_policies:::engine
    engine_production_recipe_engine:::engine
    engine_production_rollback:::engine
    engine_production_serializer:::engine
    engine_production_verification:::engine
    engine_session_diff:::engine
    engine_session_graph:::engine
    engine_session_resolver:::engine
    engine_session_synchronizer:::engine
    engine_snapshots_manager:::engine
    engine_snapshots_serializer:::engine
    engine_sound_capabilities_cache:::engine
    engine_sound_capabilities_discovery:::engine
    engine_sound_capabilities_registry:::engine
    engine_sound_chains_builder:::engine
    engine_sound_chains_models:::engine
    engine_sound_chains_templates:::engine
    engine_sound_context:::engine
    engine_sound_curator_auto_curate:::engine
    engine_sound_drum_rack_authentic_builder:::engine
    engine_sound_drum_rack_engine:::engine
    engine_sound_drum_rack_models:::engine
    engine_sound_drum_rack_resolver:::engine
    engine_sound_drum_rack_verifier:::engine
    engine_sound_engine:::engine
    engine_sound_evolution:::engine
    engine_sound_foley_texture:::engine
    engine_sound_intent:::engine
    engine_sound_linter:::engine
    engine_sound_macros_mappings:::engine
    engine_sound_macros_semantic_morph:::engine
    engine_sound_macros_system:::engine
    engine_sound_parameters_curves:::engine
    engine_sound_parameters_mapper:::engine
    engine_sound_parameters_semantic:::engine
    engine_sound_presets_resolver:::engine
    engine_sound_presets_scoring:::engine
    engine_sound_profiles_models:::engine
    engine_sound_profiles_profiles:::engine
    engine_sound_snapshots_snapshots:::engine
    engine_sound_vital_builder:::engine
    engine_sound_vital_file_manager:::engine
    engine_sound_vital_models:::engine
    engine_supervisor_acoustic_probe:::engine
    engine_supervisor_anti_cliche_guard:::engine
    engine_supervisor_failure_diagnostics:::engine
    engine_supervisor_gatekeeper:::engine
    engine_supervisor_governance:::engine
    engine_transactions_manager:::engine
    engine_transactions_rollback:::engine
    engine_transactions_validator:::engine
    engine_vocal_chopper:::engine
    engine_vocal_lyric_engine:::engine
    engine_vocal_pipeline:::engine
    engine_vocal_vocal_staging_supervisor:::engine
    engine_production_copilot_guided_session --> engine_knowledge_composition_chords
    engine_arrangement_fx_ear_candy_transitions --> engine_arrangement_fx_ear_candy
    engine_production_copilot_guided_session --> engine_music_melody_topline
    engine_production_copilot_stepper --> engine_mix_multitrack_sidechain
    engine_production_copilot_guided_session --> engine_memory_user_learning
    engine_production_copilot_recipes --> engine_music_models
    engine_production_copilot_guided_session --> engine_mix_psychoacoustic_masking
    engine_arrangement_linter_linter --> engine_arrangement_models_section
    engine_audio_deconstruction_reconstructor --> engine_audio_deconstruction_models
    engine_arrangement_templates_genres --> engine_arrangement_templates_structures
    engine_arrangement_drops_engine --> engine_arrangement_models_section
    engine_music_harmony_full_song --> engine_music_theory_notes
    engine_music_melody_vocal_hook --> engine_music_models
    engine_production_full_song_producer --> engine_fx_device_parameter_supervisor
    engine_production_copilot_stepper --> engine_arrangement_automation_live_automation
    engine_sound_vital_file_manager --> engine_sound_vital_models
    engine_production_copilot_role_orchestrator --> engine_music_harmony_full_song
    engine_arrangement_compiler --> engine_arrangement_models_song
    engine_arrangement_transitions_engine --> engine_arrangement_transitions_pre_drop
    engine_production_copilot_guided_session --> engine_knowledge_composition_scales
    engine_instruments_plugins_normalizer --> engine_fx_device_parameter_supervisor
    engine_production_copilot_guided_session --> engine_music_drums_genre_grooves
    engine_music_drums_ghost_notes --> engine_music_models
    engine_production_recipe_engine --> engine_mix_sidechain_manager
    engine_production_copilot_recipes --> engine_mastering_live_master_chain
    engine_music_melody_topline --> engine_music_models
    engine_production_full_song_producer --> engine_instruments_browser_catalog
    engine_production_copilot_stepper --> engine_music_melody_counterpoint
    engine_production_copilot_stepper --> engine_mix_sidechain_manager
    engine_production_copilot_guided_session --> engine_mastering_live_master_chain
    engine_arrangement_transitions_engine --> engine_arrangement_models_section
    engine_production_copilot_guided_session --> engine_music_drums_ghost_notes
    engine_music_groove_humanizer --> engine_music_models
    engine_production_copilot_stepper --> engine_instruments_drum_rack_guard
    engine_production_copilot_guided_session --> engine_knowledge_plugins_ozone12
    engine_arrangement_blueprints_song_arranger --> engine_arrangement_fx_ear_candy
    engine_arrangement_roles_matrix --> engine_arrangement_models_section
    engine_arrangement_generator --> engine_arrangement_energy_curve
    engine_production_copilot_recipes --> engine_vocal_vocal_staging_supervisor
    engine_sound_vital_builder --> engine_sound_vital_models
    engine_production_copilot_guided_session --> engine_knowledge_arrangement_song_structures
    engine_production_full_song_producer --> engine_mix_multitrack_sidechain
    engine_production_copilot_guided_session --> engine_instruments_browser_catalog
    engine_music_bass_intelligent_808 --> engine_music_models
    engine_audio_live_listener --> engine_mix_loudness_analyzer
    engine_mastering_release_package --> engine_audio_stem_audit
    engine_knowledge_plugins_plugin_chains --> engine_knowledge_constants
    engine_arrangement_energy_curve --> engine_arrangement_models_section
    engine_arrangement_transitions_risers --> engine_music_models
    engine_production_copilot_guided_session --> engine_audio_live_listener
    engine_arrangement_scoring --> engine_arrangement_models_section
    engine_production_copilot_stepper --> engine_sound_curator_auto_curate
    engine_production_copilot_recipes --> engine_mix_spatial_depth
    engine_audio_deconstruction_separator --> engine_audio_deconstruction_models
    engine_arrangement_generator --> engine_arrangement_variation_planner
    engine_sound_drum_rack_engine --> engine_instruments_drum_map
    engine_production_full_song_producer --> engine_arrangement_transitions_risers
    engine_production_copilot_guided_session --> engine_mix_render_manager
    engine_arrangement_blueprints_song_arranger --> engine_arrangement_automation_live_automation
    engine_production_copilot_guided_session --> engine_mix_static_auditor
    engine_production_copilot_guided_session --> engine_production_copilot_stepper
    engine_arrangement_compiler --> engine_instruments_library_preset_catalog
    engine_production_copilot_guided_session --> engine_music_mutation_engine
    engine_music_harmony_reharmonizer --> engine_music_models
    engine_production_full_song_producer --> engine_music_harmony_full_song
    engine_production_copilot_stepper --> engine_music_expression_mpe
    engine_production_copilot_recipes --> engine_arrangement_blueprints_song_arranger
    engine_indexer_manifest --> engine_indexer_storage
    engine_production_copilot_stepper --> engine_production_copilot_role_orchestrator
    engine_music_drums_genre_grooves --> engine_music_models
    engine_production_full_song_producer --> engine_music_melody_vocal_hook
    engine_production_copilot_guided_session --> engine_mix_loudness_standards
    engine_production_copilot_guided_session --> engine_instruments_drum_rack_guard
    engine_arrangement_transitions_engine --> engine_arrangement_transitions_models
    engine_production_copilot_stepper --> engine_music_models
    engine_production_copilot_guided_session --> engine_music_harmony_full_song
    engine_production_copilot_role_orchestrator --> engine_instruments_installed_scanner
    engine_arrangement_blueprints_song_arranger --> engine_mix_channel_strip
    engine_production_copilot_recipes --> engine_mix_sidechain
    engine_arrangement_generator --> engine_arrangement_templates_structures
    engine_sound_drum_rack_resolver --> engine_instruments_library_resolver
    engine_production_full_song_producer --> engine_music_harmony_strum
    engine_music_melody_vocal_hook --> engine_music_harmony_full_song
    engine_production_copilot_stepper --> engine_music_drums_evolver
    engine_music_drums_evolver --> engine_music_models
    engine_production_copilot_guided_session --> engine_mix_lufs_validation_gate
    engine_production_copilot_guided_session --> engine_knowledge_plugins_fabfilter
    engine_arrangement_fx_ear_candy --> engine_music_models
    engine_arrangement_compiler --> engine_music_intent
    engine_production_copilot_role_orchestrator --> engine_music_bass_intelligent_808
    engine_mix_spatial_depth --> engine_music_models
    engine_production_copilot_guided_session --> engine_fx_device_parameter_supervisor
    engine_music_melody_topline --> engine_music_harmony_full_song
    engine_production_copilot_stepper --> engine_instruments_installed_scanner
    engine_production_copilot_guided_session --> engine_music_harmony_strum
    engine_production_full_song_producer --> engine_arrangement_transitions_impacts
    engine_production_copilot_recipes --> engine_music_drums_multitrack
    engine_production_copilot_stepper --> engine_mix_channel_strip
    engine_production_copilot_stepper --> engine_music_bass_intelligent_808
    engine_arrangement_variation_planner --> engine_arrangement_models_section
    engine_indexer_manifest --> engine_indexer_fileinfo
    engine_arrangement_generator --> engine_arrangement_roles_orchestrator
    engine_arrangement_compiler --> engine_arrangement_models_section
    engine_audio_deconstruction_expressive_transcriber --> engine_music_models
    engine_arrangement_generator --> engine_arrangement_locking
    engine_music_bass_intelligent_808 --> engine_music_harmony_full_song
    engine_production_recipe_engine --> engine_arrangement_automation_weaver
    engine_production_copilot_stepper --> engine_vocal_chopper
    engine_indexer_manifest --> engine_indexer_parser
    engine_production_copilot_stepper --> engine_mix_gain_staging_auto_stager
    engine_production_copilot_guided_session --> engine_knowledge_sampling_sampling
    engine_fx_device_parameter_supervisor --> engine_instruments_browser_catalog
    engine_production_copilot_role_orchestrator --> engine_music_melody_topline
    engine_production_copilot_stepper --> engine_audio_stem_audit
    engine_sound_macros_system --> engine_sound_parameters_mapper
    engine_instruments_browser_catalog --> engine_instruments_installed_scanner
    engine_production_copilot_guided_session --> engine_arrangement_automation_live_automation
    engine_production_copilot_stepper --> engine_mix_fader_rider
    engine_arrangement_generator --> engine_arrangement_templates_genres
    engine_production_copilot_role_orchestrator --> engine_music_models
    engine_production_full_song_producer --> engine_instruments_installed_scanner
    engine_arrangement_blueprints_song_arranger --> engine_arrangement_models_section
    engine_arrangement_transitions_impacts --> engine_arrangement_impacts_downlifters
    engine_production_copilot_stepper --> engine_presets_analog_lab_ui_automator
    engine_arrangement_blueprints_song_arranger --> engine_mastering_live_master_chain
    engine_production_copilot_recipes --> engine_music_bass_glide
    engine_production_copilot_recipes --> engine_mix_sidechain_manager
    engine_vocal_vocal_staging_supervisor --> engine_vocal_pipeline
    engine_production_copilot_guided_session --> engine_mix_sidechain_manager
    engine_production_copilot_recipes --> engine_arrangement_fx_ear_candy
    engine_production_full_song_producer --> engine_mix_channel_strip
    engine_production_full_song_producer --> engine_music_bass_intelligent_808
    engine_production_copilot_stepper --> engine_music_melody_topline
    engine_production_boundary --> engine_transactions_manager
    engine_knowledge_composition_drum_patterns --> engine_knowledge_constants
    engine_arrangement_blueprints_song_arranger --> engine_mix_sidechain_manager
    engine_music_harmony_strum --> engine_music_groove_pocket
    engine_production_copilot_stepper --> engine_mix_phase_alignment
    engine_fx_device_parameter_supervisor --> engine_supervisor_governance
    engine_knowledge_composition_chords --> engine_knowledge_constants
    engine_audio_chopper_transient --> engine_music_models
    engine_production_copilot_stepper --> engine_arrangement_transitions_pre_drop
    engine_knowledge_composition_scales --> engine_knowledge_constants
    engine_production_copilot_recipes --> engine_music_groove_pocket
    engine_production_copilot_guided_session --> engine_music_groove_pocket
    engine_indexer_walker --> engine_indexer_keywords
    engine_production_copilot_stepper --> engine_audio_chopper_transient
    engine_production_copilot_recipes --> engine_music_harmony_reharmonizer
    engine_production_recipe_engine --> engine_mastering_live_master_chain
    engine_vocal_chopper --> engine_music_models
    engine_production_recipe_engine --> engine_audio_sample_generator
    engine_production_copilot_stepper --> engine_mastering_live_master_chain
    engine_production_copilot_guided_session --> engine_arrangement_transitions_automation
    engine_production_copilot_guided_session --> engine_supervisor_anti_cliche_guard
    engine_arrangement_linter_linter --> engine_arrangement_linter_comparison
    engine_production_copilot_stepper --> engine_music_drums_ghost_notes
    engine_instruments_browser_catalog --> engine_production_copilot_role_orchestrator
    engine_music_expression_mpe --> engine_music_models
    engine_arrangement_templates_genres --> engine_arrangement_models_section
    engine_production_recipe_engine --> engine_vocal_vocal_staging_supervisor
    engine_production_full_song_producer --> engine_music_melody_topline
    engine_production_copilot_stepper --> engine_instruments_browser_catalog
    engine_production_copilot_stepper --> engine_music_groove_pool
    engine_production_copilot_guided_session --> engine_production_recipe_engine
    engine_production_full_song_producer --> engine_arrangement_transitions_pre_drop
    engine_audio_deconstruction_transcriber --> engine_audio_deconstruction_separator
    engine_production_copilot_guided_session --> engine_production_copilot_role_orchestrator
    engine_audio_live_listener --> engine_forensics_models
    engine_music_harmony_strum --> engine_music_models
    engine_arrangement_narrative_arc --> engine_arrangement_models_section
    engine_audio_live_listener --> engine_mix_loudness_standards
    engine_production_full_song_producer --> engine_sound_drum_rack_authentic_builder
    engine_arrangement_generator --> engine_arrangement_compiler
    engine_production_copilot_guided_session --> engine_music_models
    engine_production_full_song_producer --> engine_mastering_live_master_chain
    engine_production_copilot_stepper --> engine_midi_program_change
    engine_production_copilot_guided_session --> engine_knowledge_plugins_vocal_chains
    engine_audio_deconstruction_transcriber --> engine_audio_deconstruction_models
    engine_production_full_song_producer --> engine_music_drums_ghost_notes
    engine_production_recipe_engine --> engine_supervisor_governance
    engine_production_copilot_stepper --> engine_mix_frequency_slotting
    engine_production_copilot_stepper --> engine_mastering_release_package
    engine_production_copilot_stepper --> engine_presets_catalog
    engine_production_copilot_stepper --> engine_supervisor_governance
    engine_production_copilot_guided_session --> engine_music_drums_evolver
    engine_music_melody_counterpoint --> engine_music_models
    engine_production_copilot_stepper --> engine_arrangement_transitions_risers
    engine_arrangement_generator --> engine_arrangement_linter_linter
    engine_production_copilot_guided_session --> engine_instruments_installed_scanner
    engine_production_copilot_guided_session --> engine_knowledge_plugins_serum2
    engine_mastering_mastering_analyzer --> engine_mix_loudness_analyzer
    engine_production_copilot_recipes --> engine_mix_eq_resonance
    engine_arrangement_blueprints_song_arranger --> engine_music_drums_multitrack
    engine_arrangement_generator --> engine_arrangement_models_song
    engine_production_copilot_role_orchestrator --> engine_fx_device_parameter_supervisor
    engine_production_copilot_stepper --> engine_music_groove_humanizer
    engine_music_harmony_full_song --> engine_music_models
    engine_production_copilot_stepper --> engine_music_harmony_full_song
    engine_arrangement_density --> engine_arrangement_models_section
    engine_production_recipe_engine --> engine_music_drums_genre_grooves
    engine_production_copilot_stepper --> engine_mix_sidechain
    engine_production_copilot_guided_session --> engine_knowledge_producers_producers
    engine_production_copilot_guided_session --> engine_music_bass_intelligent_808
    engine_production_copilot_guided_session --> engine_indexer_manifest
    engine_production_copilot_stepper --> engine_mix_eq_dynamic_eq
    engine_production_copilot_role_orchestrator --> engine_instruments_browser_catalog
    engine_production_copilot_stepper --> engine_arrangement_impacts_downlifters
    engine_production_copilot_stepper --> engine_music_melody_vocal_hook
    engine_production_full_song_producer --> engine_mix_fader_rider
    engine_production_copilot_guided_session --> engine_arrangement_automation_weaver
    engine_production_full_song_producer --> engine_arrangement_fx_ear_candy_transitions
    engine_indexer_manifest --> engine_indexer_walker
    engine_production_recipe_engine --> engine_fx_device_parameter_supervisor
    engine_arrangement_generator --> engine_arrangement_roles_matrix
    engine_audio_deconstruction_neural_separator --> engine_audio_deconstruction_separator
    engine_arrangement_templates_structures --> engine_arrangement_models_section
    engine_production_copilot_stepper --> engine_fx_device_parameter_supervisor
    engine_production_boundary --> engine_session_graph
    engine_production_copilot_guided_session --> engine_mix_gain_staging_auto_stager
    engine_production_full_song_producer --> engine_mastering_release_package
    engine_arrangement_linter_comparison --> engine_arrangement_models_section
    engine_audio_live_listener --> engine_forensics_analyzer
    engine_production_copilot_stepper --> engine_sound_foley_texture
    engine_production_copilot_stepper --> engine_music_harmony_strum
    engine_indexer_parser --> engine_indexer_keywords
    engine_arrangement_generator --> engine_arrangement_scoring
    engine_arrangement_transitions_pre_drop --> engine_arrangement_transitions_models
    engine_production_copilot_guided_session --> engine_audio_stem_audit
    engine_arrangement_transitions_impacts --> engine_music_models
    engine_production_copilot_stepper --> engine_music_drums_multitrack
    engine_audio_deconstruction_neural_separator --> engine_audio_deconstruction_models
    engine_production_boundary --> engine_adapters_mock_adapter
    engine_production_copilot_guided_session --> engine_audio_stem_bouncer
    engine_knowledge_composition_basslines --> engine_knowledge_constants
    engine_arrangement_generator --> engine_arrangement_models_section
    engine_arrangement_generator --> engine_arrangement_transitions_engine
    engine_arrangement_generator --> engine_arrangement_drops_engine
    engine_music_harmony_full_song --> engine_music_theory_scales
    engine_production_copilot_stepper --> engine_arrangement_transitions_impacts
    engine_arrangement_roles_orchestrator --> engine_arrangement_roles_matrix
    engine_vocal_vocal_staging_supervisor --> engine_mix_frequency_slotting
```
