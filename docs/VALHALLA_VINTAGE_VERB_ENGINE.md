# Valhalla VintageVerb Engine Manual & Technical Reference

Este documento detalla la arquitectura, el modelo intermedio (IR), la investigación exhaustiva de los 22 modos algorítmicos, el validador en 3 niveles, las políticas acústicas anti-barro y el motor de inyección por portapapeles para **Valhalla VintageVerb** (`.vpreset`).

---

## 1. Misión y Posicionamiento Acústico

**Valhalla VintageVerb** actúa como el pilar de **reverberación algorítmica de estudio vintage** (emulaciones de hardware de finales de los 70 y principios de los 80 como Lexicon 224, Lexicon 480L y EMT 250), complementando a **Valhalla Supermassive** (especializado en feedback delay networks cósmicos y colas masivas):

```
                              Espacialidad y Modulación
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     [ Valhalla VintageVerb ]                        [ Valhalla Supermassive ]
  Reverberación de Estudio Clásica                Redes de Delay & Reverb Cósmica
• Ambientes de batería, rooms apretados          • Colas infinitas, paisajes cinemáticos
• Placas vocales sedosas, halls de mezcla       • Delays rítmicos sincronizados a BPM
• 22 Modos de Sala/Placa/Cámara                 • 22 Constelaciones de retardo
• 3 Eras Tonales (1970s, 1980s, Now)            • Modulación masiva y chorus envolvente
• Control estricto de pre-delay y decaimiento   • Ecos difusos no lineales
```

---

## 2. Los 22 Modos Algorítmicos Oficiales

Cada modo emula una topología de líneas de retardo entrelazadas, filtros de dispersión y densidad de difusión característica:

| Índice | Nombre del Modo | Carácter Acústico | Densidad | Aplicación Óptima |
| :---: | :--- | :--- | :--- | :--- |
| `0` | `Concert Hall` | Espacio grande, balanceado, cálido y envolvente | Media-Alta | Cuerdas, pianos de cola, sintetizadores analógicos |
| `1` | `Bright Hall` | Reflexiones brillantes y presencia en frecuencias altas | Media-Alta | Leads vocales modernos, guitarras pop |
| `2` | `Plate` | Alta densidad de difusión inmediata sin ecos discretos | Muy Alta | Cajas de batería, percusión metálica, palmas |
| `3` | `Room` | Reflexiones tempranas marcadas sin cola prolongada | Media | Baterías acústicas, rhythm guitars, percusión seca |
| `4` | `Chamber` | Difusión uniforme y balance espectral transparente | Alta | Voces principales, vientos acústicos |
| `5` | `Random Space` | Modulación estéreo aleatoria no lineal | Media-Alta | Teclados Rhodes, sintetizadores atmosféricos |
| `6` | `Chorus Space` | Modulación coral densa y brillante estilo años 80 | Alta | Guitarras clean ochenteras, polysynths |
| `7` | `Ambience` | Espacio corto de mezcla sin decaimiento perceptible | Media | Ubicación espacial 3D sin enturbiar la mezcla |
| `8` | `Sanctuary` | Caverna sacra de decaimiento masivo | Alta | Coros litúrgicos, campanas, música sacra |
| `9` | `Dirty Hall` | Saturación armónica de entrada y grano 12-bit | Media | Baterías lo-fi, hip-hop retro, texturas vintage |
| `10` | `Dirty Plate` | Placa con aspereza y distorsión armónica analógica | Alta | Snares agresivos, rock/industrial, punk |
| `11` | `Smooth Plate` | Placa moderna ultrasuave y sedosa sin asperezas | Muy Alta | Voces solistas Pop, R&B y baladas |
| `12` | `Smooth Room` | Sala sin picos resonantes ni frecuencias metálicas | Media | Pianos de estudio, guitarras clásicas |
| `13` | `Smooth Random` | Espacio aleatorio sin artefactos de modulación | Alta | Colchones de cuerdas, sintetizadores pads |
| `14` | `Nonlin` | Reverb no lineal con envolvente inversa o gated | Variable | Baterías gated de los 80s (Phil Collins), risers inversos |
| `15` | `Chaotic Hall` | Modulación de retardo basada en atractores caóticos | Media-Alta | Soundscapes cinemáticos, drones |
| `16` | `Chaotic Chamber` | Cámara con atractor no periódico asimétrico | Media | Guitarras experimentales y avant-garde |
| `17` | `Chaotic Neutral` | Modulación asimétrica pura sin inclinación tímbrica | Media | Texturas electrónicas complejas |
| `18` | `Cathedral` | Espacio sacro expansivo con decaimiento de hasta 70s | Muy Alta | Pads atmosféricos, coros etéreos, ambient |
| `19` | `Palace` | Espacio gigante noble con alta fidelidad y claridad | Alta | Pianos de concierto, ensambles sinfónicos |
| `20` | `Chamber1979` | Cámara digital de 1ª generación (Lexicon 224) | Media | Producciones synthwave, vaporwave, retro 70s |
| `21` | `Hall1984` | Hall digital de 2ª generación (Lexicon 480L) | Alta | Voces épicas de los 80s, baladas de estadio |

---

## 3. Las 3 Eras de Color Tonal (`ColorMode`)

El selector `ColorMode` reproduce fielmente las limitaciones de hardware y convertidores AD/DA de cada época:

```
  1970s (0.0) ───► Ancho de banda 10 kHz | 12-bit | Artefactos armónicos y ruido sutil analógico
  1980s (0.5) ───► Ancho de banda 15 kHz | 16-bit | Brillante con medios ricos (Lexicon 480L)
  Now   (1.0) ───► Ancho de banda 20 kHz | Full 32/64-bit | Ultra-transparente y sin colorear
```

---

## 4. Mapeo Matemático de Parámetros Físicos

El motor de sonido maneja conversiones biyectivas continuas entre unidades físicas y los valores normalizados en el rango $[0.0, 1.0]$:

### Pre-Delay
El pre-delay se expresa físicamente en milisegundos ($0.0\,\text{ms} \le t \le 500.0\,\text{ms}$):
$$p = \frac{t_{\text{ms}}}{500.0} \iff t_{\text{ms}} = p \times 500.0$$

### Decay (RT60)
El decaimiento sigue una escala logarítmica/exponencial entre $0.2\,\text{s}$ y $70.0\,\text{s}$:
$$p = \frac{\log_{10}(\text{decay} / 0.2)}{\log_{10}(70.0 / 0.2)} \iff \text{decay} = 0.2 \times \left(\frac{70.0}{0.2}\right)^p$$

### Filtros de Corte Espectral
- **LowCut**: Mapeo logarítmico entre $10\,\text{Hz}$ y $500\,\text{Hz}$.
- **HighCut**: Mapeo logarítmico entre $1000\,\text{Hz}$ y $20000\,\text{Hz}$.

---

## 5. Validador de Rangos en 3 Niveles

El módulo `ValhallaVintageVerbValidator` asegura que toda configuración generada proceduralmente o por IA sea acústicamente óptima y técnicamente válida:

```
┌────────────────────────────────────────────────────────┐
│                      Tier 1                            │
│           Límites Normalizados [0.0, 1.0]              │
│  • Todos los 16 parámetros dentro de rango estricto.   │
│  • Modos válidos (0..21) y colores canónicos (0..2).   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                      Tier 2                            │
│           Coherencia Física & Espectral                │
│  • LowCut < HighCut (Prohíbe cancelación de espectro). │
│  • Separación mínima garantizada: gap >= 0.15.         │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                      Tier 3                            │
│           Políticas Acústicas de Mezcla                │
│  • Anti-Mud: LowCut >= 0.05 en Baterías y Bajos.       │
│  • Haas Pre-delay: PreDelay <= 0.5 (<= 250ms).         │
│  • Mix Safety: Mix <= 0.85 en pistas de inserción.     │
└────────────────────────────────────────────────────────┘
```

### Auto-Sanitizador (`ValhallaVintageVerbSanitizer`)
Si un parámetro está fuera de límites o existe una inversión espectral ($LowCut \ge HighCut$), el sanitizador:
1. Clampa todos los flotantes al rango $[0.0, 1.0]$.
2. Separa los cortes espectrales automáticamente ($LowCut = \max(0.0, HighCut - 0.15)$).
3. Resuelve alias difusos: `"80s"` $\to$ `"1980s"`, `"smooth plate"` $\to$ `"Smooth Plate"`, `"gated"` $\to$ `"Nonlin"`.

---

## 6. Persistencia XML y Portapapeles de Windows

Valhalla DSP implementa una arquitectura estándar de serialización mediante cadenas XML embebidas. El módulo `ValhallaVintageVerbSerializer`:

1. Genera archivos XML `.vpreset` listos para ser almacenados en la carpeta del proyecto.
2. Inyecta la cadena XML directamente en el **Portapapeles de Windows** mediante PowerShell:
   ```powershell
   powershell -NoProfile -Command "Set-Clipboard -Value '<ValhallaVintageVerb pluginVersion=\"2.2.0\" ... />'"
   ```
3. Permite al usuario en Ableton Live hacer **clic derecho en VintageVerb $\to$ *Paste from Clipboard*** para cargar la configuración al instante.

---

## 7. Integración con el Copilot de Producción

- **Fase 5 (`phase_5_insert_effects.py`)**: Al seleccionar VintageVerb en un bus o canal, el Copilot calcula automáticamente el pre-delay Haas óptimo según el BPM ($12\,\text{ms}$ para baterías, $28\,\text{ms}$ para voces), valida el modelo, guarda el archivo `.vpreset`, copia el XML al portapapeles y despacha comandos en vivo por Live Object Model (`execute_code`).
- **Catálogo de Efectos (`role_fx_catalog.py`)**: Registrado con especificación completa de 14 parámetros en `VALHALLA_VINTAGE_VERB_PARAMS` para todos los roles armónicos y percusivos.
