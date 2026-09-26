# Surge XT Synthesizer Engine Manual & Technical Reference

Este documento detalla la arquitectura, el modelo intermedio (IR), los 10 motores osciladores, los 20+ modelos de filtros, el validador en 3 niveles, las políticas acústicas y el motor de generación procedural de parches para **Surge XT Synthesizer** (`.surgepatch`).

---

## 1. Misión y Posicionamiento Arquitectónico

**Surge XT** actúa como el **pilar de síntesis modular híbrida, modelado físico y síntesis Eurorack**, complementando tanto a **Vital** (síntesis por tablas de onda y distorsión espectral) como a **Decent Sampler** (instrumentos acústicos multi-muestreados):

```
                                  Motor de Instrumentos
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         ▼                                   ▼                                   ▼
    [ Vital Synth ]                   [ Surge XT Synth ]                [ Decent Sampler ]
 Síntesis Wavetable Digital         Síntesis Modular & Física            Muestreo Acústico
• Tablas de ondas espectrales      • Modelado Físico (String)          • Pianos de cola
• Filtros analógicos virtuales     • Modular Eurorack (Twist/Plaits)   • Cuerdas sinfónicas
• JSON zlib binario (.vital)       • FM de 2 y 3 operadores            • Instrumentos multi-capa
• Enfoque moderno Dance/Trap       • 10 Motores de Oscilador           • Árbol XML (.dspreset)
                                   • 20+ Filtros Analógicos & Combs
                                   • XML Nativo (.surgepatch)
```

---

## 2. Los 10 Tipos de Oscilador Oficiales

Cada oscilador en Surge XT puede configurarse de manera independiente en los 3 slots de la Escena A/B:

| Tipo | Nombre Técnico | Algoritmo y Arquitectura | Aplicación Óptima |
| :---: | :--- | :--- | :--- |
| `0` | `Classic` | Emulación analógica pura de ondas Diente de Sierra y Pulso con control continuo de ancho de pulso (PWM) y sub-oscilador. | Bajos analógicos, leads clásicos, pads vintage |
| `1` | `Modern` | Oscilador con saturación de tabla de onda interna y armónicos ricos antialiasing. | Leads cortantes en mezcla, bajos EDM |
| `2` | `Wavetable` | Síntesis por tablas de ondas polifónicas con interpolación espectral continua y morphing. | Sonidos evolutivos, pads complejos, sweeps |
| `3` | `Sine` | Generador senoidal puro con conformación de onda (wave-folding) y distorsión armónica par/impar. | 808 subs puros, campanas, bajos limpios |
| `4` | `FM2` | Síntesis por modulación en frecuencia con 2 operadores (Carrier y Modulator) y retroalimentación. | Teclados eléctricos cristalinos, plucks percusivos |
| `5` | `FM3` | 3 operadores FM configurables con múltiples algoritmos de modulación cruzada. | Campanas complejas, percusiones metálicas, FX |
| `6` | `String` | **Modelado físico** por guía de ondas (Karplus-Strong) con amortiguamiento no lineal y rigidez de cuerda. | Guitarras acústicas, arpas, clavinetes sintéticos |
| `7` | `Twist` | **Port oficial del oscilador Eurorack Plaits** de Mutable Instruments. Genera síntesis aditiva, formantes y modelado modal. | Leads modulares de vanguardia, ear candy |
| `8` | `Alias` | Oscilador digital con reducción intencional de sample rate y bit-crush para grano retro. | Chiptune, lo-fi beats, texturas glitch |
| `9` | `AudioIn` | Enrutamiento de señal de audio en tiempo real para usar Surge XT como procesador de filtrado y modulación. | Vocoders, filtros dinámicos, saturación externa |

---

## 3. Arquitectura de Filtros Duales y Envolventes

Surge XT implementa dos unidades de filtrado estéreo configurables en serie o paralelo:

### A. Modelos de Filtro (20+ Modelos Registrados)
- **Ladder Lowpass** ($12\,\text{dB}$ y $24\,\text{dB}$): Emulación del transistor ladder clásico estilo Moog con calidez analógica y resonancia autolimitada.
- **K35 Lowpass / Highpass**: Filtro agresivo con distorsión por diodos estilo Korg MS-20.
- **Diode Lowpass**: Respuesta no lineal de diodos estilo Roland TB-303 para líneas de bajo ácidas.
- **OB-Xd Lowpass / Bandpass / Highpass**: Emulación analógica Oberheim multi-modo de $12\,\text{dB}$ y $24\,\text{dB}$.
- **Chowdhury Tri-Pole**: Filtro moderno con saturación RK y respuesta de fase analógica.
- **Comb Filter (Positive / Negative)**: Filtro peine sintonizado para efectos de resonancia y síntesis física.

### B. Envolventes AHDSR y Motor de Unísono
- **Envolventes dedicadas de Amplitud y Filtro**: Attack, Decay, Sustain (nivel $[0, 1]$) y Release continuos en segundos.
- **Unísono de hasta 16 voces**: Permite ensanchamiento estéreo masivo (`unison_detune`) para arquetipos supersaw.

---

## 4. Validador de Rangos en 3 Niveles

El módulo `SurgeSynthValidator` garantiza que todo parche generado sea sonoro, musical y matemáticamente estable:

```
┌────────────────────────────────────────────────────────┐
│                      Tier 1                            │
│           Límites y Tipos de Oscilador                 │
│  • Tipos de oscilador y filtros canónicos válidos.     │
│  • Octava en [-3, 3], semitonos en [-12, 12].          │
│  • Niveles de oscilador y volumen en [0.0, 1.0].       │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                      Tier 2                            │
│           Integridad Física & Anti-Clicks              │
│  • Prevención de Parche Muerto (Dead Patch):           │
│    Al menos 1 oscilador activo con nivel > 0.0         │
│    y volumen global > 0.0.                             │
│  • Piso Anti-Click: Release >= 0.005s obligatorio.     │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                      Tier 3                            │
│           Políticas Acústicas & Seguridad DSP          │
│  • Resonancia Máxima Segura: Q <= 0.95                 │
│    (Evita runaway resonance y sobrecarga DSP).         │
│  • Ataque Ultra-Rápido: Attack >= 0.001s para         │
│    evitar clicks abruptos en transitorios iniciales.   │
└────────────────────────────────────────────────────────┘
```

### Auto-Sanitizador (`SurgeSynthSanitizer`)
1. **Resurrección de Parche Muerto**: Si todos los osciladores están silenciados o en nivel $0.0$, activa el oscilador 1 con tipo `Classic` a nivel $0.80$.
2. **Piso de Liberación**: Si $Release < 0.005\,\text{s}$, lo eleva automáticamente a $0.005\,\text{s}$ eliminando artefactos por cruce por cero.
3. **Resolución de Alias**: `"plaits"` $\to$ `"Twist"`, `"moog"` $\to$ `"Ladder Lowpass"`, `"karplus"` $\to$ `"String"`.

---

## 5. Fábrica de Arquetipos y Serialización XML

El módulo `SurgeSynthPatchFactory` construye parches pre-calibrados según la función acústica de la pista:

| Arquetipo | Motores | Filtro | Función en Arreglo |
| :--- | :--- | :--- | :--- |
| **Reese Bass** | 2x Classic (detuned) + 1x Sine (sub) | Ladder LP 24dB ($0.45$) | Cimiento subgrave con movimiento estéreo sutil |
| **808 Sub-Bass** | 1x Sine (direct out) | K35 LP ($0.35$) | Subgrave puro monofónico para Trap y Reggaeton |
| **FM Pluck / Keys** | 1x FM2 + 1x Sine | K35 LP ($0.70$) | Plucks cristalinos y pianos eléctricos percusivos |
| **Supersaw Lead** | 2x Classic (unison 7) + 1x Twist | OB-Xd LP 24dB ($0.80$) | Lead masivo con apertura estéreo frontal |
| **Lush Ambient Pad** | 1x Wavetable + 1x Sine (unison 4) | Chowdhury Tri-Pole ($0.65$) | Colchón armónico etéreo con ataque lento ($0.45\,\text{s}$) |

El serializador `SurgeSynthSerializer` escribe archivos nativos `.surgepatch` XML con codificación UTF-8 para su almacenamiento en el proyecto.

---

## 6. Integración en el Flujo de Producción del Copilot

- **Navegación e Instrumentos (`browser_catalog.py` & `curated_data.py`)**: Surge XT está indexado para `BASS`, `KEYS`, `LEAD` y `PAD`. Si el usuario solicita presets de Surge XT, el motor ofrece los arquetipos procedimentales o la opción limpia.
- **Escáner sin Colisiones (`installed_scanner.py`)**: `Surge XT` (sintetizador) se distingue con precisión de `Surge XT Effects` (procesador de audio FX) mediante reglas de exclusión de prefijos.
- **Fase 3 (`phase_3_instruments.py`)**: Al asignar Surge XT a un canal MIDI, el motor crea el parche adaptado al BPM y rol, lo valida, guarda el archivo `.surgepatch` y despacha los parámetros canónicos a Live mediante `set_device_parameter` por LOM.
- **Supervisión de Parámetros (`device_parameter_supervisor.py`)**: El perfil `SURGE_XT` permite gobernar filtros, envolventes y osciladores mediante `apply_semantic_tuning`.
