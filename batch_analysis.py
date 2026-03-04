"""
batch_analysis.py — Análisis masivo de números telefónicos
Lee un archivo .txt con un número por línea y analiza cada uno.
Usado por: phoneosint_tui.py (módulo [9])
"""

import json
import time
from pathlib import Path
from datetime import datetime


def analyze_batch(filepath: str, save: str = None) -> dict:
    """
    Analiza un archivo con múltiples números telefónicos.
    Args:
        filepath: ruta al archivo .txt (un número por línea)
        save:     ruta donde guardar el reporte JSON de resultados
    Returns:
        dict con resultados de todos los números
    """
    print(f"[*] Batch Analysis: {filepath}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "archivo":   filepath,
        "total":     0,
        "exitosos":  0,
        "fallidos":  0,
        "resultados": [],
    }

    # Leer archivo
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]
    except Exception as e:
        print(f"  [-] Error leyendo archivo: {e}")
        report["error"] = str(e)
        return report

    numbers = [l for l in lines if l]
    report["total"] = len(numbers)
    print(f"[+] {len(numbers)} números a analizar")

    if not numbers:
        print("  [-] Archivo vacío o sin números válidos")
        return report

    # Importar módulo de análisis
    try:
        from phoneosint import parse_number, get_basic_info, get_geo_info, get_carrier_info
        has_phoneosint = True
    except ImportError:
        has_phoneosint = False
        print("  [!] phoneosint no disponible, usando phonenumbers directo")

    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone as pntz
        has_pn = True
    except ImportError:
        has_pn = False
        print("  [-] phonenumbers no instalado")
        print("      pip install phonenumbers --break-system-packages")

    # Analizar cada número
    for i, number in enumerate(numbers, 1):
        print(f"\n[{i}/{len(numbers)}] Analizando: {number}")
        entry = {
            "numero": number,
            "estado": "error",
        }

        try:
            if has_phoneosint:
                parsed = parse_number(number)
                if parsed:
                    entry["basico"]   = get_basic_info(parsed)
                    entry["geo"]      = get_geo_info(parsed)
                    entry["operador"] = get_carrier_info(parsed)
                    entry["estado"]   = "ok"
                    report["exitosos"] += 1
                    print(f"  [+] {entry['geo'].get('País/Región', 'N/A')} | {entry['operador'].get('Operador (es)', 'N/A')}")
                else:
                    entry["error"] = "Número inválido"
                    report["fallidos"] += 1
                    print(f"  [-] Número inválido")

            elif has_pn:
                try:
                    parsed = phonenumbers.parse(number, None)
                    if phonenumbers.is_valid_number(parsed):
                        pais = geocoder.description_for_number(parsed, "es")
                        op   = carrier.name_for_number(parsed, "es")
                        zones = list(pntz.time_zones_for_number(parsed))
                        entry["pais"]     = pais
                        entry["operador"] = op
                        entry["zonas"]    = zones
                        entry["estado"]   = "ok"
                        report["exitosos"] += 1
                        print(f"  [+] {pais} | {op}")
                    else:
                        entry["error"] = "Número inválido"
                        report["fallidos"] += 1
                except Exception as e:
                    entry["error"] = str(e)
                    report["fallidos"] += 1
            else:
                entry["error"] = "Sin módulos de análisis disponibles"
                report["fallidos"] += 1

        except Exception as e:
            entry["error"] = str(e)
            report["fallidos"] += 1
            print(f"  [-] Error: {e}")

        report["resultados"].append(entry)

        # Pequeña pausa para no saturar
        if i < len(numbers):
            time.sleep(0.3)

    # Resumen
    print(f"\n[+] Batch completado:")
    print(f"    Total:    {report['total']}")
    print(f"    Exitosos: {report['exitosos']}")
    print(f"    Fallidos: {report['fallidos']}")

    # Guardar reporte
    if save:
        try:
            Path(save).parent.mkdir(parents=True, exist_ok=True)
            with open(save, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"[+] Reporte guardado: {save}")
        except Exception as e:
            print(f"  [-] Error guardando: {e}")

    return report
