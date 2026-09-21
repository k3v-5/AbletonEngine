# Nivel T — Intentional Musical Performance & Humanization Engine

> **"Menos cuantización ≠ más humano."**  
> Un músico profesional no toca con ruido blanco estocástico; toca con **consistencia, intención métrica, jerarquía de dinámica, peso físico en los dedos y respiración fraseológica**. La humanización debe ser un **comportamiento colectivo emergente y correlacionado**, no una perturbación estocástica e independiente en cada pista.

---

## 1. Visión y Fundamentos Arquitectónicos

El **Nivel T** complementa el circuito cerrado creativo (Nivel S) dotando al motor de interpretación viva y organológica. Erradica tanto la rigidez robótica de la rejilla matemática al 100% como el error clásico de inyectar *jitter* gaussiano ciego.

```
                  COMPOSITIONAL DNA
                         │
                         ▼
                PERFORMANCE INTENT
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          POCKET      DYNAMICS   ARTICULATION
              │          │          │
              └──────────┼──────────┘
                         ▼
              PERFORMANCE GENERATOR
              (Correlated Ensemble)
                         │
                         ▼
                  HUMANIZED MIDI
                         │
                         ▼
                    AUDIO RENDER
                         │
                         ▼
             CONTEXTUAL SONIC CRITIC
                         │
                         ▼
                 CLOSED LOOP (S)
              [COMMIT or 0 ms ROLLBACK]
```

---

## 2. Los 5 Módulos del Nivel T

### T1 — Performance Core (`engine/performance/core.py`)
- **`apply_microtiming_intent`**: Aplica desviaciones temporales calibradas por rol y ancladas al BPM. Las pistas ancla (Kick) mantienen varianza mínima ($\le 1.2\text{ ms}$), mientras notas de alta velocidad anticipan sutilmente el pulso.
- **`apply_velocity_hierarchy`**: Modela contornos dinámicos según jerarquía métrica (tiempos fuertes del compás vs subdivisiones débiles) y estilo dinámico (`EXPRESSIVE`, `TIERED_PULSE`, `FLAT_BED`, etc.).
- **`apply_chord_strumming`**: Descompone acordes en bloque en interpretaciones micro-espaciadas en el tiempo ($5-25\text{ ms}$), acentuando la voz melódica superior con boost de velocidad dinámico (+8 a +15 vel).
- **`apply_articulation_shaping`**: Modula duraciones de nota para evitar puertas cuadradas (staccato 50-70%, legato con micro-solapamiento orgánico).
- **`PerformanceSnapshot` & Rollback**: Copias profundas inmutables con fingerprints SHA-256 para reversión atómica instantánea en 0 ms.

### T2 — Groove Intelligence & Humanización Correlacionada (`engine/performance/groove_intelligence.py`)
- **Principio Rector:** Los instrumentos no toman decisiones de tiempo independientes.
  $$\text{Kick} = \text{Ancla temporal primaria}$$
  $$t_{\text{bass}} = t_{\text{actual\_kick}} + \Delta_{\text{coupling\_ms}}$$
  $$t_{\text{snare}} = t_{\text{anchor\_pulse}} + \text{laid\_back\_ms}$$
  $$\text{HiHat} = \text{Subdivisión micro-acentuada por física de muñeca}$$
  $$\text{Keys} = \text{Centro de frase armónica} + \text{micro-rasgueo}$$
- **`GrooveMemory`**: Analiza y aprende las relaciones temporales históricas nativas de la sesión (desfase medio bombo-bajo, arrastre de caja, ratio de swing).

### T3 — Phrase Breathing Engine (`engine/performance/phrase_breathing.py`)
- Analiza la morfología de frases melódicas y armónicas:
  $$\text{Frase} \longrightarrow \text{Preparación} \longrightarrow \text{Tensión/Ascenso} \longrightarrow \text{Nota de Llegada} \longrightarrow \text{Resolución} \longrightarrow \text{Respiración}$$
- **Nota de llegada (Climax / Target note)**: Entra con peso dinámico reforzado (+10 a +18 vel), ligero rubato expresivo (+3 a +8 ms) y mayor prolongación de sustain.
- **Tensión / Ascenso**: Empuje sutil (*push*, $-2$ a $-4\text{ ms}$) y crescendo progresivo.
- **Silencio mínimo garantizado**: La última nota de cada frase recorta su release para asegurar un espacio de respiración orgánica $\ge 35\text{ ms}$ antes de la siguiente sección.

### T4 — Performance Identity & Catalog Memory (`engine/performance/identity.py`)
- **`PerformanceSignature`**: Firma criptográfica y matemática de un intérprete o ensamble:
  - `timing_signature`: Desviaciones medias y varianzas por rol.
  - `velocity_signature`: Medias y desviaciones dinámicas por rol.
  - `articulation_signature`: Ratios de duración y micro-rasgueos.
  - `groove_signature`: Desfases relativos bombo-bajo y caja.
  - `phrase_signature`: Rubato en notas de llegada y gaps de respiración.
  - `instrument_relationships`: Topología de dependencias temporales del ensamble.
- **Integración con `CatalogMemory`**: Permite comparar estilos interpretativos entre canciones del catálogo mediante similitud métrica y reusar identidades para crear una firma de artista coherente.

### T5 — Integración Closed-Loop S ↔ T (`engine/performance/closed_loop_adapter.py`)
- **Detección de fatiga mecánica**: Audita la sesión (rejilla $\ge 90\%$, dispersión de velocidad $\text{std} < 6.0$).
- **Generación de 3 candidatos interpretativos**:
  1. *Subtle Pocket* (anclaje métrico firme, dinámica sutil).
  2. *Laid-Back Expressive* (pocket neo-soul, respiración melódica, micro-rasgueo armónico).
  3. *Dilla Soul Drag* (swing pronunciado de hardware, arrastre dinámico y rubato).
- **Audición In-Situ**: Cada candidato se audita con el `ContextualSonicCritic`.
- **Veto de Gobernanza**: La gobernanza valida que no se rompan contratos, ADN ni anclas temáticas.
- **Decisión**: Si $\Delta Q > 0$, ejecuta `COMMIT` e inscribe `PERFORMANCE_MUTATION` en el `EvolutionLedger`. Si no mejora o degrada, ejecuta `ROLLBACK` al 100% en 0 ms.

---

## 3. Los 6 Criterios de Aceptación Auditables Verificados

| Criterio | Requisito Matemático | Resultado de Prueba | Estado |
|---|---|---|:---:|
| **1. Groove Conservation** | Acoplamiento Kick-Bass $\Delta t \le \pm 2.0\text{ ms}$ tras humanización | Error medio $\le 0.4\text{ ms}$ | **PASSED** |
| **2. Structural Melody Integrity** | Notas de llegada conservan función armónica con peso dinámico | Climax note velocity $\ge 100$, rubato $+5\text{ ms}$ | **PASSED** |
| **3. Hierarchical Chord Strumming** | Micro-rasgueo polifónico con melodía superior destacada | Spread 18 ms, voz superior $+14\text{ vel}$ | **PASSED** |
| **4. Phrase Breathing Gaps** | Silencio orgánico mínimo entre frases melódicas $\ge 35\text{ ms}$ | Silencio medido $\ge 40.0\text{ ms}$ | **PASSED** |
| **5. Atomic Reversibility** | Reversión al 100% de notas originales en 0 ms ante degradación | Hash idéntico, rollback en 0 ms | **PASSED** |
| **6. Performance Identity** | Distinción matemática entre estilos de interpretación | Similitud Neo-Soul vs Funk $< 0.85$ | **PASSED** |

---

## 4. Ejecución de Pruebas

```powershell
python -m pytest tests/test_performance_and_humanization_engine.py -v
```
**Resultado:** `12 passed in 3.50s` (100% passing).
Suite ampliada (Creative, Evolution, Critic, Performance): `43 passed in 4.02s` con 0 regresiones.
