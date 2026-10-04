# 🎛️ Guía y Especificación de Controles Modulares Avanzados de Producción Multiplatino

**AbletonEngine - Arquitectura de Producción Parametrizada y Soberanía Cognitiva de la IA**  
**Versión:** 2.0.0 Multi-Platinum  
**Objetivo:** Exponer a la IA el control total, explícito y desacoplado de las técnicas de producción más sofisticadas de la industria musical (Finneas, Kevin Parker, Mike Shinoda, Max Martin, Metro Boomin), garantizando que el motor sea agnóstico y esté preparado para **cualquier género**.

---

## 1. Principio Rector de la Arquitectura

1. **Soberanía Absoluta de la IA:** El motor **nunca** asume valores por defecto ni decide en secreto por la IA. El motor expone los controles, rangos numéricos reales, y la IA decide qué módulos aplican a la visión artística de la canción.
2. **Modularidad Desacoplada:** Cada uno de los 6 módulos avanzados opera de forma independiente; se pueden encender todos, combinaciones selectivas, o ninguno (en caso de producciones acústicas minimalistas).
3. **Validación Pedagógica sin Sobrescritura:** Si la IA define una configuración acústicamente conflictiva para el género (ej. swing borracho en un techno industrial 4-on-the-floor), el motor **emite una alerta explicativa** detallando la colisión psicoacústica, pero **no sobrescribe silenciosamente** la decisión de la IA.

---

## 2. Catálogo Oficial de los 6 Módulos Avanzados (`advanced_production`)

El bloque JSON `advanced_production` en el Manifiesto de Diseño de la Fase 0 se estructura de la siguiente manera:

```json
{
  "advanced_production": {
    "crossover_stacking": { ... },
    "turnarounds_and_silences": { ... },
    "groove_and_pocket": { ... },
    "spatial_narrative": { ... },
    "ear_candy": { ... },
    "master_dynamics": { ... }
  }
}
```

---

### Módulo 1: `crossover_stacking` (Diseño Sonoro y Capas Psicoacústicas)
Divide el instrumento focal (típicamente el bajo, lead o sintes principales) en 3 capas de frecuencia complementarias para asegurar máxima potencia en sistemas de club y traducción perfecta a altavoces de teléfono móvil:

| Parámetro | Tipo | Rango / Opciones | Descripción Técnica & Musical |
|---|---|---|---|
| `enabled` | `bool` | `true / false` | Activa o desactiva la división de capas por frecuencia. |
| `target_roles` | `List[str]` | `["BASS", "808_BASS", "LEAD", "SYNTH"]` | Roles a los que se aplica el apilamiento de capas. |
| `sub_crossover_hz` | `float` | `60.0 - 120.0` (Hz) | Frecuencia de corte entre Sub y Mid. Típico: 90.0 Hz. |
| `air_crossover_hz` | `float` | `1000.0 - 3500.0` (Hz) | Frecuencia de corte entre Mid y Air. Típico: 1200.0 Hz. |
| `sub_mono_strict` | `bool` | `true / false` | Fuerza a la capa sub a ser 100% monofónica (sin phase smearing). |
| `mid_saturation_drive` | `float` | `0.0 - 1.0` | Nivel de distorsión armónica/cinta en el rango medio (150-1200 Hz). |
| `top_stereo_width` | `float` | `1.0 - 1.8` | Apertura estéreo en frecuencias altas (>1200 Hz). |

*Uso por Género:* Indispensable en Nu-Metal, Dark Pop, Synthwave, Dubstep, Trap, Tech House. Innecesario en Lo-Fi orgánico o Folk puro.

---

### Módulo 2: `turnarounds_and_silences` (Transiciones, Micro-Silencios y Caídas)
Gobierna la variación estructural en el compás 8 de cada frase para evitar la monotonía cíclica:

| Parámetro | Tipo | Rango / Opciones | Descripción Técnica & Musical |
|---|---|---|---|
| `enabled` | `bool` | `true / false` | Activa las variaciones de transición en los compases finales. |
| `vacuum_stops` | `bool` | `true / false` | Silencia súbitamente todos los instrumentos de base en el compás previo al drop para crear un vacío dramático. |
| `vacuum_duration_beats` | `float` | `0.5 - 2.0` (beats) | Duración del micro-silencio. Típico: 1.0 beat (tiempo 4 del compás 8). |
| `preserve_solo_element` | `str` | `"NONE", "VOCAL_WHISPER", "REVERB_TAIL", "SNARE_SNAP"` | Elemento aislado que queda flotando durante el silencio. |
| `drum_fills` | `bool` | `true / false` | Inyecta redobles sincopados de toms y caja en los compases de transición. |
| `fill_velocity_crescendo`| `bool` | `true / false` | Rampa ascendente de velocidad MIDI (ej: 75 -> 120) en el redoble. |
| `kick_dropout_in_fill` | `bool` | `true / false` | Mutea el bombo en los beats 3 y 4 del compás de fill para no saturar los graves. |
| `analog_tape_stop` | `bool` | `true / false` | Efecto de desaceleración de cinta analógica (pitch y volumen cayendo). |
| `tape_stop_semitones` | `float` | `-6.0` a `-24.0` (st) | Caída de afinación de la parada de cinta. Típico: -12.0 st. |
| `tape_stop_scope` | `str` | `"MUSIC_BUS_ONLY", "MASTER_BUS"` | Si se aplica solo a la música (dejando la batería seca) o al master. |

*Uso por Género:* Crítico en Pop, Rock, EDM, Trap, Alternative, Hyperpop. Opcional en Minimal Techno o Jazz.

---

### Módulo 3: `groove_and_pocket` (Humanización Asimétrica y Swing de Hardware)
Rompe la rigidez robótica con micro-desfases fisiológicos calibrados por instrumento:

| Parámetro | Tipo | Rango / Opciones | Descripción Técnica & Musical |
|---|---|---|---|
| `pocket_style` | `str` | `"neo_soul_dilla", "atlanta_trap", "boom_bap", "french_pump", "dark_rage", "organic_human", "straight_precise"` | Modelo de micro-timing de referencia. |
| `snare_dragging_ms` | `float` | `-10.0` a `+25.0` (ms) | Retraso intencional de la caja respecto al beat. Valores positivos (+12ms) dan el efecto *laid-back* de Kevin Parker / J Dilla. |
| `sub_dragging_ms` | `float` | `0.0` a `+10.0` (ms) | Retraso del bajo respecto al bombo (+4 a +6ms) para que el transitorio del bombo respire antes de la entrada del subgrave. |
| `hihat_swing_pct` | `float` | `50.0 - 72.0` (%) | Porcentaje de swing de semicorcheas emulando hardware MPC 60 / SP-1200. (50% = sin swing, 58% = swing natural, 66% = tresillos puros). |
| `chord_strum_spread_ms` | `float` | `0.0 - 30.0` (ms) | Desfase progresivo entre las notas de un acorde de guitarra o piano emulando la mano del músico. |
| `humanize_velocity_jitter` | `int` | `0 - 16` | Desviación estándar de velocity gaussiana por nota. |

*Uso por Género:*
- `neo_soul_dilla`: Indie Psychedelic, Neo-Soul, R&B, Bedroom Pop.
- `atlanta_trap`: Trap moderno, Drill, Rage.
- `boom_bap`: Hip-hop noventero, Lo-Fi, Trip-Hop.
- `french_pump`: House, French Touch, Nu-Disco.
- `straight_precise`: Trance, Techno, Synthpop Ochentero.

---

### Módulo 4: `spatial_narrative` (Arquitectura Tridimensional del Campo Estéreo)
Evita la mezcla estática haciendo que el campo estéreo respire dinámicamente con la narrativa emocional:

| Parámetro | Tipo | Rango / Opciones | Descripción Técnica & Musical |
|---|---|---|---|
| `enabled` | `bool` | `true / false` | Activa la automatización dinámica de ancho estéreo en `Utility`. |
| `verse_width_pct` | `float` | `50.0 - 85.0` (%) | Ancho estéreo en estrofas (intimidad, foco central). |
| `chorus_width_pct` | `float` | `120.0 - 160.0` (%) | Ancho estéreo en estribillos (sensación física masiva envolvente). |
| `bridge_width_pct` | `float` | `80.0 - 110.0` (%) | Ancho estéreo en puentes de transición. |
| `bass_mono_cutoff_hz`| `float` | `80.0 - 140.0` (Hz) | Todo el audio por debajo de esta frecuencia es forzado a Mono estricto. Típico: 110.0 Hz. |
| `abbey_road_reverb_filter` | `bool` | `true / false` | Aplica filtro paso-alto en 350 Hz y paso-bajo en 7 kHz a las pistas de retorno de Reverb. |
| `reverb_sidechain_ducking` | `bool` | `true / false` | Atenúa la cola de reverberación mientras el instrumento o la voz líder están sonando. |

*Uso por Género:* Obligatorio en Pop Multiplatino, Rock de Estadio, Indie Rock, Hyperpop, EDM, Trap.

---

### Módulo 5: `ear_candy` (Eventos Memorables y Micro-Detalles Sónicos)
Coloca micro-eventos únicos en los valles de densidad para captar la atención del cerebro del oyente:

| Parámetro | Tipo | Rango / Opciones | Descripción Técnica & Musical |
|---|---|---|---|
| `enabled` | `bool` | `true / false` | Activa la inyección de micro-eventos. |
| `max_events_per_song` | `int` | `1 - 3` | Regla de oro: 1 o 2 eventos memorables por canción, jamás saturación. |
| `allowed_types` | `List[str]` | `["DELAY_THROW", "NOISE_SWEEP_VACUUM", "VOCAL_WHISPER_CHOP", "PITCH_DROP_GLIDE", "REVERSE_PIANO_SWELL"]` | Tipos de micro-eventos autorizados por la IA. |
| `delay_throw_spike` | `bool` | `true / false` | Automatiza el envío auxiliar de delay al 100% en la última sílaba de una estrofa y lo corta en 0%. |
| `dynamic_auto_pan` | `bool` | `true / false` | Movimiento sinusoidal sutil de izquierda a derecha en elementos de fondo durante la subida. |

*Uso por Género:* Fundamental en canciones de Billie Eilish, Rosalía, Travis Scott, Gorillaz, Kevin Parker.

---

### Módulo 6: `master_dynamics` (Dinámica Master, Soft Clipping y Calibración LUFS)
Garantiza máxima competitividad comercial sin fatiga auditiva ni bombeo del limitador:

| Parámetro | Tipo | Rango / Opciones | Descripción Técnica & Musical |
|---|---|---|---|
| `soft_clipper_pre_limiter` | `bool` | `true / false` | Coloca un Saturator en curva `Analog Clip` antes del limitador para afeitar picos de 2ms sin alterar el timbre audible. |
| `clipper_drive_db` | `float` | `0.0 - 4.0` (dB) | Ganancia de entrada al soft clipper. Típico: 1.5 dB. |
| `nyc_parallel_drums` | `bool` | `true / false` | Activa compresión paralela agresiva estilo Nueva York en el bus de batería. |
| `nyc_mix_blend_pct` | `float` | `10.0 - 25.0` (%) | Proporción de batería aplastada sumada por debajo de la señal limpia. |
| `target_lufs` | `float` | `-7.0` a `-14.0` (LUFS) | Objetivo de sonoridad integrado según el género. |
| `true_peak_ceiling_dbtp` | `float` | `-1.0` a `-0.3` (dBTP) | Techo máximo de pico real para evitar distorsión inter-sample en streaming (Spotify, Apple Music). |

---

## 3. Ejemplo Completo de Especificación JSON en Fase 0

A continuación se muestra un ejemplo real de cómo la IA puede enviar su configuración avanzada en la Fase de Diseño:

```json
{
  "song_name": "Borderline_Echoes",
  "artist": "Tame Impala",
  "genre": "Indie_Psychedelic",
  "bpm": 118.0,
  "time_signature": "4/4",
  "key": "D",
  "scale": "natural_minor",
  "climax_bar": 72,
  "advanced_production": {
    "crossover_stacking": {
      "enabled": true,
      "target_roles": ["BASS"],
      "sub_crossover_hz": 85.0,
      "air_crossover_hz": 1100.0,
      "sub_mono_strict": true,
      "mid_saturation_drive": 0.35,
      "top_stereo_width": 1.25
    },
    "turnarounds_and_silences": {
      "enabled": true,
      "vacuum_stops": true,
      "vacuum_duration_beats": 1.0,
      "preserve_solo_element": "REVERB_TAIL",
      "drum_fills": true,
      "fill_velocity_crescendo": true,
      "kick_dropout_in_fill": true,
      "analog_tape_stop": true,
      "tape_stop_semitones": -12.0,
      "tape_stop_scope": "MUSIC_BUS_ONLY"
    },
    "groove_and_pocket": {
      "pocket_style": "neo_soul_dilla",
      "snare_dragging_ms": 14.0,
      "sub_dragging_ms": 6.0,
      "hihat_swing_pct": 59.0,
      "chord_strum_spread_ms": 16.0,
      "humanize_velocity_jitter": 7
    },
    "spatial_narrative": {
      "enabled": true,
      "verse_width_pct": 70.0,
      "chorus_width_pct": 145.0,
      "bridge_width_pct": 90.0,
      "bass_mono_cutoff_hz": 110.0,
      "abbey_road_reverb_filter": true,
      "reverb_sidechain_ducking": true
    },
    "ear_candy": {
      "enabled": true,
      "max_events_per_song": 2,
      "allowed_types": ["DELAY_THROW", "NOISE_SWEEP_VACUUM"],
      "delay_throw_spike": true,
      "dynamic_auto_pan": true
    },
    "master_dynamics": {
      "soft_clipper_pre_limiter": true,
      "clipper_drive_db": 1.5,
      "nyc_parallel_drums": true,
      "nyc_mix_blend_pct": 15.0,
      "target_lufs": -12.0,
      "true_peak_ceiling_dbtp": -0.8
    }
  }
}
```

---

## 4. Guía de Selección Rápida por Géneros (Matriz de Recomendaciones)

| Género / Estilo | Pocket Style | Snare Drag | Tape Stop | Stereo Width Riding | Crossover Bass | Target LUFS |
|---|---|---|---|---|---|---|
| **Dark ASMR Pop** (Billie Eilish) | `organic_human` | +6 ms | Sí (Compás 32) | 65% Verso / 135% Coro | Sí (Sub Sine + Whisper Mid) | -9.0 LUFS |
| **Indie Psychedelic** (Tame Impala)| `neo_soul_dilla`| **+14 ms** | Sí (Music Bus) | 70% Verso / 145% Coro | Sí (Vintage Bass) | -12.0 LUFS |
| **Nu-Metal / Rock** (Linkin Park) | `boom_bap` | +8 ms | No (Picos secos)| 80% Verso / 150% Coro | Sí (Distorted Mid Bass) | -8.5 LUFS |
| **Atlanta Trap** (Metro Boomin) | `atlanta_trap` | +8 ms | Sí (Dropouts) | 90% Verso / 130% Coro | Sí (808 Sub + Distorted Mid)| -7.5 LUFS |
| **Peak-Time Techno** | `straight_precise`| **0 ms** | No (Continuidad)| 100% Verso / 120% Coro | Sí (Sub Rumble Mono) | -8.0 LUFS |
| **French Touch / House** | `french_pump` | +2 ms | Sí (Sidechain pump)| 85% Verso / 135% Coro | No (Bass clásico con filtro)| -9.0 LUFS |
| **Bedroom Pop / Lo-Fi** | `lofi_sp1200` | +12 ms | Sí (Vinyl stop)| 75% Verso / 110% Coro | No (Bajo cálido saturado) | -13.0 LUFS |
| **Reggaeton Moderno** | `reggaeton_dembow`| +4 ms | Sí (Silencio 1 beat)| 85% Verso / 130% Coro | Sí (808 subgrave limpio) | -8.0 LUFS |

---

## 5. Protocolo de Validación Acústica del Motor

El motor ejecuta la siguiente rutina pedagógica al recibir la especificación de diseño:

1. **Chequeo de Rangos Físicos:** Asegura que ningún valor numérico sature o crasheé la API LOM de Ableton Live (ej. velocidades entre 1 y 127, frecuencias entre 20 y 20,000 Hz, panning entre -1.0 y +1.0).
2. **Chequeo de Compatibilidad de Género:** Si se detecta una discrepancia (ej. `snare_dragging_ms > 10.0` en un género `Tech_House` o `Hardstyle`), el validador emite:
   ```
   ⚠️ ADVERTENCIA ACÚSTICA: El género 'Tech_House' depende de una rejilla 4-on-the-floor rígida.
   Un snare dragging de +14.0 ms puede desalinear la pegada con el bombo.
   ¿Deseas mantener este desfase como un experimento deliberado o prefieres ajustar a 0.0 - 2.0 ms?
   ```
3. **No-Sobrescritura:** El motor jamás cambia el valor de la IA a menos que la IA explícitamente envíe la corrección.
