"""
timezone_inference.py — Análisis de Zona Horaria
Infiere zona horaria del número y estima hora local.
Usado por: phoneosint_tui.py (módulo [4])
"""

import json
from datetime import datetime
from pathlib import Path

try:
    import phonenumbers
    from phonenumbers import timezone as pntz
except ImportError:
    phonenumbers = None

try:
    import pytz
except ImportError:
    pytz = None


def _get_current_time_in_zone(tz_name: str) -> str:
    """Retorna la hora actual en una zona horaria dada."""
    if not pytz:
        return "pytz no disponible"
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: {e}"


def _infer_activity(hora_activo: str, zones: list) -> list:
    """
    Dado que el número estuvo activo a cierta hora local del analista,
    infiere la hora equivalente en las zonas del número.
    """
    if not hora_activo or not pytz:
        return []

    results = []
    try:
        h, m = map(int, hora_activo.split(":"))
        # Asumimos hora del analista en UTC para simplificar
        analyst_tz = pytz.UTC
        now = datetime.now(analyst_tz)
        activity_time = now.replace(hour=h, minute=m, second=0, microsecond=0)

        for tz_name in zones:
            try:
                target_tz = pytz.timezone(tz_name)
                local_time = activity_time.astimezone(target_tz)
                results.append({
                    "zona":        tz_name,
                    "hora_local":  local_time.strftime("%H:%M %Z"),
                    "offset":      local_time.strftime("%z"),
                })
            except Exception:
                continue
    except Exception:
        pass
    return results


def run_timezone_analysis(number: str, hora_activo: str = None, save: str = None) -> dict:
    """
    Analiza zona horaria del número telefónico.
    - number: número en formato E.164
    - hora_activo: hora en que se detectó actividad (HH:MM)
    - save: ruta donde guardar el reporte JSON
    """
    print(f"[*] Timezone Analysis: {number}")
    report = {
        "numero":      number,
        "timestamp":   datetime.now().isoformat(),
        "zonas":       [],
        "hora_activo": hora_activo,
        "inferencia":  [],
        "hora_actual_por_zona": {},
    }

    if not phonenumbers:
        print("  [-] phonenumbers no instalado")
        print("      pip install phonenumbers --break-system-packages")
        report["error"] = "phonenumbers no instalado"
        return report

    # 1. Parsear número
    try:
        parsed = phonenumbers.parse(number, None)
        if not phonenumbers.is_valid_number(parsed):
            print("  [-] Número inválido")
            report["error"] = "Número inválido"
            return report
    except Exception as e:
        print(f"  [-] Error al parsear: {e}")
        report["error"] = str(e)
        return report

    # 2. Obtener zonas horarias
    zones = list(pntz.time_zones_for_number(parsed))
    report["zonas"] = zones

    if not zones:
        print("  [-] No se encontraron zonas horarias")
    else:
        print(f"[+] Zonas detectadas: {', '.join(zones)}")
        for z in zones:
            hora_actual = _get_current_time_in_zone(z)
            report["hora_actual_por_zona"][z] = hora_actual
            print(f"  • {z}: {hora_actual}")

    # 3. Inferencia de actividad
    if hora_activo:
        print(f"\n[*] Inferencia para hora activo {hora_activo} UTC...")
        inferencias = _infer_activity(hora_activo, zones)
        report["inferencia"] = inferencias
        for inf in inferencias:
            print(f"  → {inf['zona']}: {inf['hora_local']} (UTC{inf['offset']})")
        if not inferencias:
            print("  [-] No se pudo inferir (requiere pytz)")
            print("      pip install pytz --break-system-packages")

    # 4. Info adicional del número
    try:
        from phonenumbers import geocoder, carrier
        region = phonenumbers.region_code_for_number(parsed)
        pais   = geocoder.description_for_number(parsed, "es")
        op     = carrier.name_for_number(parsed, "es")
        report["pais"]     = pais
        report["region"]   = region
        report["operador"] = op
        print(f"\n[+] País: {pais} | Región: {region} | Operador: {op}")
    except Exception:
        pass

    # 5. Guardar reporte
    if save:
        try:
            Path(save).parent.mkdir(parents=True, exist_ok=True)
            with open(save, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n[+] Reporte guardado: {save}")
        except Exception as e:
            print(f"  [-] Error guardando: {e}")

    return report
