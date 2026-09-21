# Nivel R — Contextual Sonic Critic: Evaluación In-Situ y Cierre de Bucles Acústicos

## 1. Filosofía y Diagnóstico del Problema

Hasta el Nivel Q, el motor contaba con capacidades avanzadas de diseño sonoro (`TechniqueCatalog`, `SonicMutationLab`), auto-muestreo autógeno (`SelfSamplingEngine`) y evaluación estética preliminar (`GenerativeTasteEngine`).

Sin embargo, existía una brecha conceptual decisiva:

> **"Un sonido puede ser excelente aisladamente y horrible dentro del arreglo. ¿Cómo sabe el motor cuándo una transformación realmente mejora la canción en contexto?"**

Un sonido de Rhodes procesado con modulación densa y distorsión armónica puede obtener un puntaje sobresaliente en solo, pero al insertarse en el **Hook 3**:
- Podría invadir el corredor vocal ($1.0 - 3.5\text{ kHz}$) en $+3.0\text{ dB}$, volviendo ininteligible la voz principal.
- Podría acumular exceso de energía en $200 - 500\text{ Hz}$ (zona de lodo), asfixiando el bombo y el bajo.
- Podría presentar problemas de correlación de fase mono (anti-fase), cancelándose en reproducción mono.
- O, por el contrario, podría ser una **variación sutil** del motivo ($15\%$ de distancia) que refuerza la memoria de la canción, o un **descubrimiento radical** ($92\%$ de distancia) que introduce el ear candy más memorable de la obra.

El **`ContextualSonicCritic`** resuelve esta incógnita comparando físicamente dos señales de audio:
1. El render de la sección **ANTES** de la intervención (`baseline_audio`).
2. El render de la sección **DESPUÉS** de insertar la mutación (`staged_audio`).

Y responde con rigor matemático y psicoacústico a la pregunta:
> **"Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?"**

---

## 2. Las 10 Dimensiones de Evaluación Acústica y Psicoacústica

El crítico evalúa el impacto de la inserción a través de 10 dimensiones objetivas:

| Dimensión | Enfoque Acústico / Psicoacústico | Indicador Crítico / Umbral de Veto |
| :--- | :--- | :--- |
| **1. Groove & Pocket** | Estabilidad del pulso rítmico y pegada del golpe grave. | Pérdida de cresta rítmica ($> 3.0\text{ dB}$) o correlación subgraves $< 0.70$. |
| **2. Vocal Clearance** | Espacio e inteligibilidad en el corredor lírico ($1.0 - 3.5\text{ kHz}$). | Veto si $\Delta \text{Vocal} > +2.2\text{ dB}$ (`VOCAL_MASKING_EXCEEDED`). |
| **3. Spectral Crowding** | Detección de acumulación en la zona de lodo ($200 - 500\text{ Hz}$) y fuga subgrave. | Veto si $\Delta \text{Mud} > +3.2\text{ dB}$ (`MUD_ZONE_CONGESTION`). |
| **4. Transient Punch** | Factor de cresta ($\text{Peak dBFS} - \text{RMS dBFS}$), pegada de transitorios. | Veto si pérdida de cresta $> 3.5\text{ dB}$ (`TRANSIENTS_CRUSHED`). |
| **5. Energy Trajectory** | Ajuste dinámico a la narrativa de la sección (Hook vs Verse vs Bridge). | En Hook se premia lift energético ($+0.4$ a $+3.0\text{ dB}$). |
| **6. Space & Width** | Compatibilidad mono y expansión del campo estéreo Mid/Side. | Veto absoluto si correlación mono $< 0.05$ (`MONO_PHASE_COLLAPSE`). |
| **7. Identity Elevation** | Huella tímbrica distintiva frente a relleno genérico. | Bonificación por armónicos orgánicos derivados de la obra. |
| **8. Motif Resonance** | Fidelidad y resonancia del motivo melódico/armónico principal. | Clasificación según perfil de distancia perceptual. |
| **9. Sectional Contrast** | Paso textural y dinámico perceptible respecto a secciones adyacentes. | Medición del paso dinámico y expansión estéreo. |
| **10. Net Improvement ($\Delta Q$)** | **Delta holístico de calidad musical y acústica.** | Veredicto: $\ge +0.10$ (Mejora), $0.0 - 0.10$ (Marginal), $< 0$ (Degradación). |

---

## 3. Flexibilización de la Regla de Distancia Perceptual

La distancia acústica ($\Delta$) entre el sonido padre y el sonido hijo deja de ser un filtro binario ciego ($0.25 \le \Delta \le 0.88$). Pasa a clasificarse en **tres categorías descriptivas** gobernadas por el `ContextualSonicCritic`:

```
                       DISTANCIA PERCEPTUAL (Δ)
  0.0 ────────────── 0.25 ───────────────────────── 0.88 ────────────── 1.0
   │                  │                             │                  │
   ▼                  ▼                             ▼                  ▼
┌───────────────────────┐┌───────────────────────────┐┌───────────────────────┐
│  SUBTLE_RECOGNIZABLE  ││    BALANCED_EVOLUTION     ││   RADICAL_DISCOVERY   │
│       VARIATION       ││    (Parentesco Áureo)     ││ (Metamorfosis Audaz)  │
└───────────────────────┘└───────────────────────────┘└───────────────────────┘
  • Mantiene el motivo    • Equilibrio entre           • Sorpresa tímbrica
    reconocible al 100%     coherencia y frescura        extrema (ear candy)
  • No se rechaza: si     • Instrumentos de apoyo      • No se rechaza: si la
    funciona en mezcla,     y pads derivados             mezcla lo asimila bien,
    es temáticamente vital                               es una joya creativa
```

El principio rector ahora es:
> **"La distancia describe el parentesco; el `ContextualSonicCritic` decide si la mutación aporta valor real a la obra."**

---

## 4. Diagrama de Flujo del Ciclo Cerrado

```
                              NECESIDAD MUSICAL
                         (ej. "dark_floating_texture")
                                      │
                                      ▼
                           RENDER BEFORE SAMPLE (DAW)
                            Establece audio raíz
                                      │
                                      ▼
                        5 HIPÓTESIS CONCURRENTES
                         (Role-Dependent Mutations)
                                      │
                                      ▼
                           GENERATIVE TASTE ENGINE
                         Filtro estético multidimensional
                                      │
                                      ▼
                          AUDICIÓN IN-SITU EN SECCIÓN
                        (Contextual Sonic Critic A/B)
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
     BASELINE AUDIO                                       STAGED AUDIO
    (Sección antes de                                  (Sección con la
      la mutación)                                       mutación puesta)
            │                                                   │
            └─────────────────────────┬─────────────────────────┘
                                      │
                                      ▼
                         ANÁLISIS DE 10 DIMENSIONES
                    (Vocal, Mud, Crest, Mono, Energy, ...)
                                      │
                       ┌──────────────┴──────────────┐
                       ▼                             ▼
                 [ΔQ >= +0.10]                 [ΔQ < 0.0 o Veto]
             DEFINITIVE IMPROVEMENT               DEGRADATION
                       │                             │
                       ▼                             ▼
             Commit en Ableton Live        Rechazo con Directiva
             Registro de Familia Sonora    (ej. "Requiere sidechain en
             en Memoria Creativa            2.2 kHz o atenuar fader")
```

---

## 5. Ejemplo de Reporte Contextual (`ContextualAuditReport`)

```json
{
  "section_name": "Hook 3",
  "target_role": "pad_texture",
  "candidate_id": "cand_pad_01",
  "distance_category": "balanced_evolution",
  "distance_score": 0.45,
  "deltas": {
    "delta_rms_db": 1.25,
    "delta_peak_db": 0.40,
    "delta_crest_factor_db": -0.30,
    "delta_vocal_corridor_db": 0.35,
    "delta_mud_db": 0.20,
    "delta_sub_db": 0.05,
    "delta_stereo_width": 0.12,
    "delta_mono_correlation": -0.05
  },
  "dimension_scores": {
    "groove": 0.65,
    "vocal_clearance": 0.90,
    "spectral_crowding": 0.65,
    "transients": 0.50,
    "energy_trajectory": 0.90,
    "space_width": 0.75,
    "identity": 0.65,
    "motif_resonance": 0.65,
    "sectional_contrast": 0.70,
    "net_improvement": 0.35
  },
  "net_improvement_score": 0.35,
  "verdict": "definitive_improvement",
  "veto_flags": [],
  "actionable_directive": "Aprobar e integrar Pad Texture en Hook 3 (ΔQ = +0.35): Mejora neta confirmada. Eleva la energía en +1.2 dB manteniendo despejada la voz y conservando la pegada de la base. Evolución balanceada (distancia 0.45) con parentesco orgánico."
}
```
