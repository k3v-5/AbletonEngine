# HITO 1 — PARTE 03: CONTRATO FORMAL DE MEDICIÓN Y COMPLIANCE DSP
## Production Intelligence Engine (PIE) — AbletonEngine
**Especificación Técnica y Contrato de Medición Acústica v1.0**  
**Fecha de Emisión:** 2026-09-04  
**Ambiente:** Python 3.13.1 (Windows AMD64)  
**Estado:** CERTIFICADO & CONGELADO (Step 03 de 18)

---

## 1. Principio Arquitectónico Fundamental

El motor PIE establece un desacoplamiento estricto entre tres conceptos ortogonales:

$$\text{MEASUREMENT} \neq \text{PROFILE} \neq \text{COMPLIANCE}$$

```
                Audio Signal (np.ndarray, sr)
                             │
                             ▼
                ┌─────────────────────────┐
                │    LoudnessAnalyzer     │  (Strictly Descriptive:
                │ (Norma ITU-R BS.1770-5) │   NO master decisions)
                └────────────┬────────────┘
                             │
                             ▼
                    LoudnessMeasurement
            (integrated_lufs, true_peak_dbtp,
             loudness_range_lra, crest_factor)
                             │
                             ▼
                ┌─────────────────────────┐
                │ LoudnessProfile.evaluate│  (Pure, Deterministic,
                │(EBU_R128/STREAMING/CLUB)│   Side-Effect Free)
                └────────────┬────────────┘
                             │
                             ▼
                 LoudnessComplianceResult
               (profile_compliant, target_met,
                true_peak_margin_db, violations)
```

1. **Measurement (`LoudnessMeasurement`):**  
   Responde a la pregunta: **¿Qué mide físicamente la señal de audio?**  
   Describe de manera objetiva los valores de sonoridad integrada, sonoridad de corto plazo (short-term), sonoridad momentánea, rango de sonoridad (LRA), True Peak en dBTP, pico de muestra en dBFS y factor de cresta.  
   *Regla:* `LoudnessAnalyzer` sólo mide; desconoce conceptos como `STREAMING`, `CLUB`, `EBU_R128`, o decisiones como "hace falta más volumen" o "aplicar limitador".

2. **Profile (`LoudnessProfile`):**  
   Responde a la pregunta: **¿Contra qué especificación o target estamos evaluando?**  
   Encapsula de forma inmutable (`frozen=True`) los targets acústicos, tolerancias, límites de reducción de ganancia y techos de True Peak.

3. **Compliance (`LoudnessComplianceResult`):**  
   Responde a la pregunta: **¿Cumple la medición con el perfil seleccionado?**  
   Realiza una evaluación matemática pura, determinista y sin efectos secundarios, indicando violaciones en orden canónico estricto.

---

## 2. Guardrails Conceptuales Críticos

- **`-14 LUFS` no es una ley universal de streaming:** Es un target operativo adoptado por PIE. Cada plataforma comercial (Spotify, Apple Music, YouTube, Tidal) implementa algoritmos de normalización y metadatos con márgenes variables.
- **El perfil `CLUB` no es un estándar internacional:** Es un perfil de producción acústica propio de PIE ($-7.5\text{ LUFS}$) diseñado para maximizar pegada y preservar factor de cresta en sistemas de sonido de alta potencia.
- **La reducción de ganancia (Gain Reduction) no es una medición de loudness:** Corresponde a la respuesta de procesamiento de procesadores dinámicos (limitadores/compresores) y no pertenece a `LoudnessMeasurement`.
- **True Peak $\neq$ Sample Peak:** El pico discreto (`sample_peak_dbfs`) solo observa las muestras digitales; el True Peak (`true_peak_dbtp`) evalúa picos inter-sample analógicos reconstruidos mediante sobremuestreo $4\times$ sinc FIR (Anexo 2 de ITU-R BS.1770-5).

---

## 3. Especificación de Contratos Tipados

### 3.1 `MeasurementMetadata`
```python
@dataclass(frozen=True)
class MeasurementMetadata:
    standard: str = "ITU-R BS.1770-5"
    standard_version: str = "BS.1770-5 (2023)"
    algorithm_version: str = "1.0.0"
    sample_rate: int = 44100
    bit_depth: int = 24
    channel_layout: str = "stereo"
    duration_seconds: float = 0.0
    measurement_window: str = "integrated"
```
**Validación en Constructor:**
- Rechaza `sample_rate <= 0` o `bit_depth <= 0`.
- Rechaza `duration_seconds < 0`, `NaN` o `Inf`.
- Rechaza campos de texto vacíos o con solo espacios.
- Restringe `measurement_window` al conjunto cerrado: `{"momentary", "short_term", "integrated", "true_peak", "sample_peak"}`.
- Restringe `channel_layout` al conjunto cerrado: `{"mono", "stereo", "5.1", "7.1", "unknown"}`.

### 3.2 `LoudnessMeasurement`
```python
@dataclass(frozen=True, init=False)
class LoudnessMeasurement:
    integrated_lufs: float
    short_term_lufs: float
    momentary_lufs: float
    loudness_range_lra: float
    true_peak_dbtp: float
    sample_peak_dbfs: float
    crest_factor_db: float
    measurement_valid: bool
    metadata: MeasurementMetadata
    status: MeasurementStatus
```
**Propiedades:**
- Inmutable (`frozen=True`) para proteger la evidencia causal contra alteraciones accidentales en memoria.
- Validación estricta con `math.isfinite()` en todos los campos numéricos DSP (rechazo de `NaN`, `+Inf`, `-Inf`).
- Alias de compatibilidad hacia atrás: `true_peak_dbfs` redirige de forma transparente a `true_peak_dbtp`.
- Serialización determinista a JSON en `to_dict()`.

### 3.3 `LoudnessProfile`
```python
@dataclass(frozen=True)
class LoudnessProfile:
    name: str
    target_lufs: float
    tolerance_lufs: float
    max_true_peak_dbtp: float
    max_gain_reduction_db: float
    lra_target_min: Optional[float] = None
    lra_target_max: Optional[float] = None
    allow_clipping: bool = False
    policy_id: str = "STANDARD_DELIVERY"
    profile_type: ProfileType = ProfileType.STANDARD
    description: str = ""
```
**Perfiles Canónicos Iniciales:**
1. **`EBU_R128` (STANDARD):** $-23.0\text{ LUFS} \pm 0.5$, $\le -1.0\text{ dBTP}$, max GR $2.0\text{ dB}$ (guardrail PIE), $\text{LRA} \le 14.0\text{ LU}$.
2. **`STREAMING` (RECOMMENDATION):** $-14.0\text{ LUFS} \pm 1.0$, $\le -1.0\text{ dBTP}$, max GR $2.5\text{ dB}$, $\text{LRA} \ge 4.0\text{ LU}$.
3. **`CLUB` (PIE_POLICY):** $-7.5\text{ LUFS} \pm 1.0$, $\le -0.3\text{ dBTP}$, max GR $3.0\text{ dB}$, $\text{LRA} \ge 3.0\text{ LU}$.

### 3.4 `LoudnessComplianceResult`
```python
@dataclass(frozen=True)
class LoudnessComplianceResult:
    profile_name: str
    profile_compliant: bool
    measurement_valid: bool
    loudness_error_lu: float
    true_peak_margin_db: float
    lra_compliant: Optional[bool]
    violations: Tuple[str, ...]
    warnings: Tuple[str, ...]
```
**Orden Canónico Determinista de Violaciones:**
1. `MEASUREMENT_INVALID` (si la medición no es computable o es inválida)
2. `LOUDNESS_OUT_OF_RANGE` (si $| \text{loudness\_error\_lu} | > \text{tolerance\_lufs}$)
3. `TRUE_PEAK_EXCEEDED` (si $\text{true\_peak\_margin\_db} < 0$)
4. `LRA_BELOW_MINIMUM` (si $\text{lra} < \text{lra\_target\_min}$)
5. `LRA_ABOVE_MAXIMUM` (si $\text{lra} > \text{lra\_target\_max}$)
6. `CLIPPING` (si no se autoriza clipping y $\text{true\_peak\_dbtp} > 0$)

---

## 4. Pruebas de Frontera y Certificación

La suite formal `tests/test_bs1770_5_loudness.py` implementa 25 pruebas unitarias exhaustivas con 100% de éxito:

| Prueba | Caso Evaluado | Valor Entrada | Resultado Esperado | Resultado Real |
| :--- | :--- | :---: | :---: | :---: |
| **Test 21a** | LUFS Frontera Inferior Streaming | $-15.000\text{ LUFS}$ | `PASS` (target_met=True) | **PASS** |
| **Test 21b** | LUFS Frontera Nominal Streaming | $-14.000\text{ LUFS}$ | `PASS` (target_met=True) | **PASS** |
| **Test 21c** | LUFS Frontera Superior Streaming | $-13.000\text{ LUFS}$ | `PASS` (target_met=True) | **PASS** |
| **Test 21d** | LUFS Infracción por Exceso | $-12.999\text{ LUFS}$ | `FAIL` (target_met=False) | **PASS** |
| **Test 21e** | LUFS Infracción por Defecto | $-15.001\text{ LUFS}$ | `FAIL` (target_met=False) | **PASS** |
| **Test 22a** | True Peak por debajo del techo | $-1.001\text{ dBTP}$ | `PASS` (true_peak_safe=True) | **PASS** |
| **Test 22b** | True Peak en el límite exacto | $-1.000\text{ dBTP}$ | `PASS` (true_peak_safe=True) | **PASS** |
| **Test 22c** | True Peak superando el techo | $-0.999\text{ dBTP}$ | `FAIL` (true_peak_safe=False) | **PASS** |
| **Test 23a** | LRA por debajo del techo EBU | $13.999\text{ LU}$ | `PASS` (lra_compliant=True) | **PASS** |
| **Test 23b** | LRA en el techo exacto EBU | $14.000\text{ LU}$ | `PASS` (lra_compliant=True) | **PASS** |
| **Test 23c** | LRA superando el techo EBU | $14.001\text{ LU}$ | `FAIL` (lra_compliant=False) | **PASS** |
| **Test 24** | Medición inválida con valores conformes | `valid=False` | `FAIL` (profile_compliant=False) | **PASS** |
| **Test 25** | Pureza e inmutabilidad de evaluación | 100 runs | Dicts idénticos sin mutación | **PASS** |

---

## 5. Estado de la Suite de Pruebas Global

- **Total de pruebas en el repositorio:** **168**
- **Pruebas superadas:** **168** (100.0%)
- **Pruebas fallidas:** **0**
- **Tiempo de ejecución suite completa:** **43.46 segundos**
- **Regresiones detectadas:** **0**
