# engine/mix/ascii_spectrum.py
"""
Ascii Spectrum Visualizer & Psychoacoustic Frequency Inspector.
Renders 8-band text/ASCII spectrogram energy meters, highlights Mud Box buildups,
and computes surgical 4-band EQ Eight parameters.
"""

from typing import Dict, Any, List, Optional


class AsciiSpectrumVisualizer:
    """
    Generates text-based 8-band frequency spectrogram diagrams and analyzes
    spectral conflict zones (Mud Box, sub collision, harshness).
    """

    BANDS = [
        {"id": "sub", "name": "1. Sub", "range": "< 60 Hz"},
        {"id": "low_bass", "name": "2. Low Bass", "range": "60-150 Hz"},
        {"id": "mud_box", "name": "3. Mud Box", "range": "200-500 Hz"},
        {"id": "low_mid", "name": "4. Low Mid", "range": "500-1 kHz"},
        {"id": "mid", "name": "5. Mid", "range": "1-3 kHz"},
        {"id": "presence", "name": "6. Presence", "range": "3-6 kHz"},
        {"id": "brilliance", "name": "7. Brilliance", "range": "6-10 kHz"},
        {"id": "air", "name": "8. Air", "range": "10-20 kHz"},
    ]

    # Energy profiles in [0..10] bars and dBFS approximations per role
    ROLE_PROFILES: Dict[str, Dict[str, Any]] = {
        "KICK": {
            "energies": [9, 10, 4, 3, 5, 2, 1, 1],
            "notes": "Pico masivo en 50-80 Hz; posible choque con Sub 808. Requiere HPF en 28 Hz y corte leve en 300 Hz.",
            "mud_warning": False,
            "sub_warning": True,
            "recommended_eq": {
                "band_1_hpf_hz": 30.0,
                "band_2_mud_hz": 300.0,
                "band_2_gain_db": -2.5,
                "band_3_snap_hz": 3200.0,
                "band_3_gain_db": 1.5,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": -2.0,
            }
        },
        "808_BASS": {
            "energies": [10, 8, 3, 2, 1, 0, 0, 0],
            "notes": "Energía sub dominante mono. Limpiar subs inaudibles < 28 Hz para no ahogar el headroom general.",
            "mud_warning": False,
            "sub_warning": True,
            "recommended_eq": {
                "band_1_hpf_hz": 28.0,
                "band_2_mud_hz": 220.0,
                "band_2_gain_db": 1.5,  # 2nd harmonic for phone speaker translation
                "band_3_snap_hz": 1200.0,
                "band_3_gain_db": -4.0,
                "band_4_air_hz": 8000.0,
                "band_4_gain_db": -6.0,
            }
        },
        "BASS": {
            "energies": [8, 9, 5, 4, 2, 1, 0, 0],
            "notes": "Cuerpo bajo sólido. Controlar barro en 250 Hz para proteger cajas y guitarras.",
            "mud_warning": True,
            "sub_warning": True,
            "recommended_eq": {
                "band_1_hpf_hz": 32.0,
                "band_2_mud_hz": 250.0,
                "band_2_gain_db": -3.0,
                "band_3_snap_hz": 1500.0,
                "band_3_gain_db": 1.5,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": -4.0,
            }
        },
        "ELECTRIC_BASS": {
            "energies": [6, 9, 7, 5, 4, 2, 1, 0],
            "notes": "Fundamental de cuerda en 60-180 Hz y mordida de dedo/púa en 1.5 kHz. Alerta barro en 300 Hz.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 38.0,
                "band_2_mud_hz": 280.0,
                "band_2_gain_db": -3.5,
                "band_3_snap_hz": 1600.0,
                "band_3_gain_db": 2.0,
                "band_4_air_hz": 8000.0,
                "band_4_gain_db": -3.0,
            }
        },
        "DRUMS": {
            "energies": [5, 7, 6, 6, 7, 8, 9, 8],
            "notes": "Banda ancha. Peligro de barro en caja (350 Hz) y estridencia de platillos en 5-7 kHz.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 35.0,
                "band_2_mud_hz": 380.0,
                "band_2_gain_db": -3.0,
                "band_3_snap_hz": 4500.0,
                "band_3_gain_db": 1.0,
                "band_4_air_hz": 12000.0,
                "band_4_gain_db": 1.5,
            }
        },
        "DEMBOW": {
            "energies": [6, 9, 5, 5, 7, 7, 6, 4],
            "notes": "Pegada urbana concisa. HPF en 32 Hz para el 808; acento cortante en 2.8 kHz para la caja sincopada.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 32.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -2.0,
                "band_3_snap_hz": 2800.0,
                "band_3_gain_db": 2.5,
                "band_4_air_hz": 11000.0,
                "band_4_gain_db": 0.0,
            }
        },
        "KEYS": {
            "energies": [2, 4, 8, 7, 6, 4, 3, 2],
            "notes": "Acumulación severa en Mud Box (200-500 Hz). High-pass obligatorio en 100-120 Hz para dar espacio al bajo.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 110.0,
                "band_2_mud_hz": 380.0,
                "band_2_gain_db": -3.5,
                "band_3_snap_hz": 2500.0,
                "band_3_gain_db": 1.5,
                "band_4_air_hz": 11000.0,
                "band_4_gain_db": 1.0,
            }
        },
        "GUITAR": {
            "energies": [1, 3, 8, 7, 6, 5, 3, 2],
            "notes": "Resonancia hueca en 350-450 Hz. Cortar graves en 110 Hz para evitar conflicto con bombo y bajo.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 110.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -3.0,
                "band_3_snap_hz": 2800.0,
                "band_3_gain_db": 1.5,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": 1.0,
            }
        },
        "RHYTHM_GUITAR": {
            "energies": [1, 3, 8, 7, 5, 4, 2, 1],
            "notes": "Rasgueo denso con riesgo de embarrar la mezcla. HPF estricto en 120 Hz y limpieza en 400 Hz.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 120.0,
                "band_2_mud_hz": 420.0,
                "band_2_gain_db": -4.0,
                "band_3_snap_hz": 2200.0,
                "band_3_gain_db": 1.0,
                "band_4_air_hz": 9000.0,
                "band_4_gain_db": -1.0,
            }
        },
        "LEAD_GUITAR": {
            "energies": [0, 2, 5, 7, 8, 7, 4, 2],
            "notes": "Cuerpo solista en medios altos. HPF en 140 Hz y dip en 3.8 kHz si el overdrive es punzante.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 140.0,
                "band_2_mud_hz": 500.0,
                "band_2_gain_db": -1.5,
                "band_3_snap_hz": 3800.0,
                "band_3_gain_db": -2.0,  # harshness taming
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": 1.5,
            }
        },
        "PAD": {
            "energies": [2, 5, 7, 6, 5, 4, 3, 2],
            "notes": "Colchón ambiental que invade todo el espectro si no se filtra. HPF estricto en 140 Hz.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 140.0,
                "band_2_mud_hz": 350.0,
                "band_2_gain_db": -3.5,
                "band_3_snap_hz": 2000.0,
                "band_3_gain_db": -1.0,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": -2.0,
            }
        },
        "STRINGS": {
            "energies": [2, 5, 6, 6, 6, 5, 4, 3],
            "notes": "Cellos y contrabajos ensucian graves si no se cortan. HPF en 110 Hz y apertura sedosa en 10 kHz.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 110.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -2.5,
                "band_3_snap_hz": 3000.0,
                "band_3_gain_db": 1.0,
                "band_4_air_hz": 11000.0,
                "band_4_gain_db": 2.0,
            }
        },
        "BRASS": {
            "energies": [1, 4, 6, 7, 8, 7, 4, 2],
            "notes": "Mordida en 2-4 kHz. HPF en 120 Hz para evitar choques con el 808/bajo.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 120.0,
                "band_2_mud_hz": 450.0,
                "band_2_gain_db": -2.0,
                "band_3_snap_hz": 2500.0,
                "band_3_gain_db": 2.0,
                "band_4_air_hz": 9000.0,
                "band_4_gain_db": 0.5,
            }
        },
        "CHOIR": {
            "energies": [1, 3, 6, 7, 6, 5, 4, 3],
            "notes": "Formantes vocales densos. HPF en 150 Hz y corte suave en 800 Hz para no enmascarar voz líder.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 150.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -2.5,
                "band_3_snap_hz": 1800.0,
                "band_3_gain_db": -1.5,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": 2.0,
            }
        },
        "LEAD": {
            "energies": [0, 2, 4, 7, 9, 8, 5, 3],
            "notes": "Presencia frontal agresiva. Peligro de dureza digital en 3.5-4 kHz. HPF en 140 Hz.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 140.0,
                "band_2_mud_hz": 350.0,
                "band_2_gain_db": -2.0,
                "band_3_snap_hz": 3600.0,
                "band_3_gain_db": -2.5,  # anti-harshness
                "band_4_air_hz": 11000.0,
                "band_4_gain_db": 1.5,
            }
        },
        "COUNTER_LEAD": {
            "energies": [0, 1, 4, 6, 7, 7, 5, 3],
            "notes": "Debe sentarse ligeramente detrás del Lead. HPF en 160 Hz y notch en 2.5 kHz para dejar paso.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 160.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -2.5,
                "band_3_snap_hz": 2400.0,
                "band_3_gain_db": -2.0,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": 1.0,
            }
        },
        "VOCALS": {
            "energies": [1, 3, 6, 8, 9, 8, 6, 4],
            "notes": "Voz solista in-your-face. HPF estricto en 110 Hz, dip quirúrgico en 400 Hz (caja de cartón), boost de aire en 12 kHz.",
            "mud_warning": True,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 110.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -3.5,
                "band_3_snap_hz": 3200.0,
                "band_3_gain_db": 2.0,
                "band_4_air_hz": 12000.0,
                "band_4_gain_db": 2.5,
            }
        },
        "BACKING_VOCALS": {
            "energies": [0, 1, 4, 6, 6, 5, 6, 5],
            "notes": "Coros y segundas voces. HPF en 180 Hz y atenuación en 2 kHz para empujarlas detrás del lead vocal.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 180.0,
                "band_2_mud_hz": 450.0,
                "band_2_gain_db": -3.0,
                "band_3_snap_hz": 2200.0,
                "band_3_gain_db": -3.5,  # pocket for lead vocal
                "band_4_air_hz": 12000.0,
                "band_4_gain_db": 3.0,
            }
        },
        "PERCUSSION": {
            "energies": [1, 2, 4, 6, 7, 8, 7, 5],
            "notes": "Transientes afilados secundarios. HPF en 150 Hz para proteger el low-end.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 150.0,
                "band_2_mud_hz": 450.0,
                "band_2_gain_db": -2.0,
                "band_3_snap_hz": 3500.0,
                "band_3_gain_db": 1.5,
                "band_4_air_hz": 11000.0,
                "band_4_gain_db": 1.0,
            }
        },
        "EAR_CANDY": {
            "energies": [0, 0, 2, 4, 7, 8, 8, 7],
            "notes": "Destellos agudos esporádicos. HPF en 250 Hz para aislar completamente el aire y brillo.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 250.0,
                "band_2_mud_hz": 500.0,
                "band_2_gain_db": -3.0,
                "band_3_snap_hz": 4000.0,
                "band_3_gain_db": 2.0,
                "band_4_air_hz": 12000.0,
                "band_4_gain_db": 2.5,
            }
        },
        "TEXTURE_FOLEY": {
            "energies": [2, 3, 4, 5, 5, 4, 3, 2],
            "notes": "Capa orgánica a -24 dBFS. HPF en 80 Hz y corte suave en agudos para no invadir platillos.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 80.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -2.0,
                "band_3_snap_hz": 3000.0,
                "band_3_gain_db": -2.0,
                "band_4_air_hz": 10000.0,
                "band_4_gain_db": -3.0,
            }
        },
        "FX": {
            "energies": [3, 4, 5, 6, 6, 6, 5, 4],
            "notes": "Efectos dinámicos. HPF en 90 Hz para evitar sobrecarga del bus de mezcla.",
            "mud_warning": False,
            "sub_warning": False,
            "recommended_eq": {
                "band_1_hpf_hz": 90.0,
                "band_2_mud_hz": 400.0,
                "band_2_gain_db": -2.0,
                "band_3_snap_hz": 3200.0,
                "band_3_gain_db": 0.0,
                "band_4_air_hz": 11000.0,
                "band_4_gain_db": 0.0,
            }
        }
    }

    @classmethod
    def get_profile_for_role(cls, role: str) -> Dict[str, Any]:
        """Returns the profile for a role, falling back to a balanced profile."""
        norm_r = role.upper()
        if norm_r in cls.ROLE_PROFILES:
            return cls.ROLE_PROFILES[norm_r]
        for k, p in cls.ROLE_PROFILES.items():
            if k in norm_r or norm_r in k:
                return p
        return cls.ROLE_PROFILES["KEYS"]

    @classmethod
    def render_ascii_spectrum(cls, role: str, track_name: str = "") -> str:
        """
        Renders a comprehensive text/ASCII 8-band frequency spectrogram
        with energy bars and clash detection.
        """
        prof = cls.get_profile_for_role(role)
        energies = prof["energies"]
        disp_name = track_name or role

        lines = [
            f"```text",
            f"┌─────────────────────────────────────────────────────────────────────────────┐",
            f"│ 📊 ESPECTROGRAMA Y ENERGÍA FRECUENCIAL ESTIMADA: [{role}] '{disp_name}'",
            f"├─────────────────────────────────────────────────────────────────────────────┤",
            f"│ BANDA           RANGO        ENERGÍA         NIVEL   ESTADO / RIESGO        │"
        ]

        # Calculate approximate dBFS from 0..10 score (-36 dBFS to 0 dBFS)
        status_badges = {
            "sub": "🚨 COLISIÓN CON SUB/BOMBO" if prof["sub_warning"] else ("⚠️ Presencia Subgrave" if energies[0] >= 5 else "✅ Libre de Rumble"),
            "low_bass": "⚠️ Zona Fundamental Bajo" if energies[1] >= 7 else "✅ Balance Limpio",
            "mud_box": "🚨 EXCESO DE BARRO (MUD)" if prof["mud_warning"] else ("⚠️ Acumulación de Caja" if energies[2] >= 6 else "✅ Nitidez Óptima"),
            "low_mid": "✅ Cuerpo Armónico" if energies[3] >= 5 else "✅ Nivel Adecuado",
            "mid": "✅ Articulación e Inteligibilidad" if energies[4] >= 6 else "✅ Nivel Adecuado",
            "presence": "⚠️ Riesgo de Aspereza (Harsh)" if energies[5] >= 8 else "✅ Presencia Frontal",
            "brilliance": "✅ Brillo y Chasquido" if energies[6] >= 5 else "✅ Sutil",
            "air": "✅ Aire y Halo Espacial" if energies[7] >= 4 else "✅ Controlado",
        }

        for idx, b_info in enumerate(cls.BANDS):
            e_val = energies[idx]
            filled = "█" * e_val
            empty = "░" * (10 - e_val)
            approx_db = -36 + (e_val * 3.6)
            db_str = f"{approx_db:+.1f} dB".rjust(8)
            status_str = status_badges.get(b_info["id"], "✅")
            b_name = b_info["name"].ljust(15)
            b_range = b_info["range"].ljust(11)
            lines.append(f"│ {b_name} {b_range} [{filled}{empty}]  {db_str}   {status_str.ljust(22)} │")

        lines.extend([
            f"└─────────────────────────────────────────────────────────────────────────────┘",
            f"💡 DIAGNÓSTICO ACÚSTICO & RECOMENDACIONES:",
            f"• {prof['notes']}",
            f"• Preset de Ecualización Recomendado (EQ Eight):",
            f"  - Banda 1 (HPF / Low Cut): {prof['recommended_eq']['band_1_hpf_hz']:.0f} Hz",
            f"  - Banda 2 (Mud Cut / Bell): {prof['recommended_eq']['band_2_mud_hz']:.0f} Hz con {prof['recommended_eq']['band_2_gain_db']:+.1f} dB",
            f"  - Banda 3 (Presence / Notch): {prof['recommended_eq']['band_3_snap_hz']:.0f} Hz con {prof['recommended_eq']['band_3_gain_db']:+.1f} dB",
            f"  - Banda 4 (High Shelf / Air): {prof['recommended_eq']['band_4_air_hz']:.0f} Hz con {prof['recommended_eq']['band_4_gain_db']:+.1f} dB",
            f"```"
        ])

        return "\n".join(lines)
