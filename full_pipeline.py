"""
full_pipeline.py — Pipeline Completo de Análisis OSINT
Ejecuta todos los módulos en secuencia y genera reporte unificado.
Usado por: phoneosint_tui.py (módulo [0])
"""

import json
import time
from pathlib import Path
from datetime import datetime


def full_pipeline(phone: str, hora_activo: str = None, save: str = None) -> dict:
    """
    Ejecuta el pipeline completo de análisis OSINT para un número.
    Args:
        phone:       número en formato E.164 (+57...)
        hora_activo: hora en que se detectó actividad (HH:MM)
        save:        ruta donde guardar el reporte JSON unificado
    Returns:
        dict con todos los resultados
    """
    print(f"\n{'='*50}")
    print(f"  FULL PIPELINE OSINT: {phone}")
    print(f"{'='*50}\n")

    report = {
        "numero":     phone,
        "timestamp":  datetime.now().isoformat(),
        "modulos":    {},
        "resumen":    {},
    }

    # ── 1. Análisis básico ─────────────────────────────
    print("[1/5] Phone Lookup...")
    try:
        from phoneosint import parse_number, get_basic_info, get_geo_info, get_carrier_info
        parsed = parse_number(phone)
        if parsed:
            report["modulos"]["basico"]   = get_basic_info(parsed)
            report["modulos"]["geo"]      = get_geo_info(parsed)
            report["modulos"]["operador"] = get_carrier_info(parsed)
            pais = report["modulos"]["geo"].get("País/Región", "N/A")
            op   = report["modulos"]["operador"].get("Operador (es)", "N/A")
            print(f"    País: {pais} | Operador: {op}")
        else:
            report["modulos"]["basico"] = {"error": "Número inválido o no parseable"}
            print("    [-] Número no válido")
    except Exception as e:
        report["modulos"]["basico"] = {"error": str(e)}
        print(f"    [-] {e}")

    # ── 2. Timezone ────────────────────────────────────
    print("\n[2/5] Timezone Analysis...")
    try:
        from timezone_inference import run_timezone_analysis
        tz_result = run_timezone_analysis(phone, hora_activo=hora_activo)
        report["modulos"]["timezone"] = tz_result
        zonas = tz_result.get("zonas", [])
        print(f"    Zonas: {', '.join(zonas) if zonas else 'N/A'}")
    except Exception as e:
        report["modulos"]["timezone"] = {"error": str(e)}
        print(f"    [-] {e}")

    # ── 3. HLR Lookup ──────────────────────────────────
    print("\n[3/5] HLR Lookup...")
    try:
        from hlr_lookup import run_hlr
        hlr_result = run_hlr(phone)
        report["modulos"]["hlr"] = hlr_result
        op_actual = hlr_result.get("Operador Actual", hlr_result.get("Operador (local)", "N/A"))
        print(f"    Operador actual: {op_actual}")
    except Exception as e:
        report["modulos"]["hlr"] = {"error": str(e)}
        print(f"    [-] {e}")

    # ── 4. OSINT Cruzado ───────────────────────────────
    print("\n[4/5] OSINT Cruzado...")
    try:
        from osint_cruzado import run_osint
        osint_result = run_osint(phone)
        report["modulos"]["osint"] = {
            "dorks":     osint_result.get("dorks", []),
            "truecaller": osint_result.get("truecaller", {}),
            "emails":    osint_result.get("ddg", {}).get("emails_detectados", []),
            "resultados_ddg": len(osint_result.get("ddg", {}).get("principal", [])),
        }
        tc = osint_result.get("truecaller", {})
        nombre = tc.get("Nombre en Truecaller", "No encontrado")
        print(f"    Truecaller: {nombre}")
    except Exception as e:
        report["modulos"]["osint"] = {"error": str(e)}
        print(f"    [-] {e}")

    time.sleep(0.5)

    # ── 5. Resumen ejecutivo ───────────────────────────
    print("\n[5/5] Generando resumen...")
    basico  = report["modulos"].get("basico", {})
    geo     = report["modulos"].get("geo", {})
    op_mod  = report["modulos"].get("operador", {})
    hlr     = report["modulos"].get("hlr", {})
    tz      = report["modulos"].get("timezone", {})
    osint   = report["modulos"].get("osint", {})

    report["resumen"] = {
        "Número":              phone,
        "País":                geo.get("País/Región", "N/A"),
        "Código ISO":          geo.get("Código ISO País", "N/A"),
        "Tipo de Línea":       basico.get("Tipo de Línea", "N/A"),
        "Operador Registrado": op_mod.get("Operador (es)", "N/A"),
        "Operador Actual":     hlr.get("Operador Actual", hlr.get("Operador (local)", "N/A")),
        "Portado":             hlr.get("Portado", "N/A"),
        "Zona Horaria":        ", ".join(tz.get("zonas", [])) or "N/A",
        "Nombre (Truecaller)": osint.get("truecaller", {}).get("Nombre en Truecaller", "N/A"),
        "Emails encontrados":  str(len(osint.get("emails", []))),
        "Resultados web":      str(osint.get("resultados_ddg", 0)),
    }

    print("\n══ RESUMEN ══════════════════════════════════════")
    for k, v in report["resumen"].items():
        print(f"  {k:<30} {v}")

    # ── Guardar reporte ────────────────────────────────
    if save:
        try:
            Path(save).parent.mkdir(parents=True, exist_ok=True)
            with open(save, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n[+] Reporte completo guardado: {save}")
        except Exception as e:
            print(f"  [-] Error guardando: {e}")

    print(f"\n{'='*50}")
    print("  PIPELINE COMPLETADO")
    print(f"{'='*50}\n")

    return report
