"""
phoneosint.py — Análisis básico de números telefónicos
Usado por: phoneosint_tui.py (módulos [1] y [0])
"""

import json
import urllib.request
import urllib.parse

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone as pntz
    from phonenumbers import PhoneNumberType, number_type
except ImportError:
    phonenumbers = None


def parse_number(number: str):
    """Parsea un número telefónico y retorna objeto PhoneNumber o None."""
    if not phonenumbers:
        return None
    try:
        parsed = phonenumbers.parse(number, None)
        if phonenumbers.is_valid_number(parsed):
            return parsed
        # Intentar con región por defecto
        for region in ["CO", "US", "MX", "ES", "AR", "VE", "PE", "CL"]:
            try:
                parsed = phonenumbers.parse(number, region)
                if phonenumbers.is_valid_number(parsed):
                    return parsed
            except Exception:
                continue
        return None
    except Exception:
        return None


def get_basic_info(parsed) -> dict:
    """Retorna información básica del número."""
    if not parsed or not phonenumbers:
        return {}

    type_map = {
        PhoneNumberType.MOBILE: "Móvil",
        PhoneNumberType.FIXED_LINE: "Fijo",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fijo o Móvil",
        PhoneNumberType.TOLL_FREE: "Gratuito",
        PhoneNumberType.PREMIUM_RATE: "Tarifa Premium",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.UNKNOWN: "Desconocido",
    }

    ntype = number_type(parsed)

    return {
        "Número Internacional":     phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "Número E.164":             phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "Número Nacional":          phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
        "Código de País":           f"+{parsed.country_code}",
        "Número de Abonado":        str(parsed.national_number),
        "Tipo de Línea":            type_map.get(ntype, "Desconocido"),
        "Válido":                   str(phonenumbers.is_valid_number(parsed)),
        "Posible":                  str(phonenumbers.is_possible_number(parsed)),
    }


def get_geo_info(parsed) -> dict:
    """Retorna información geográfica del número."""
    if not parsed or not phonenumbers:
        return {}

    region = phonenumbers.region_code_for_number(parsed)
    desc   = geocoder.description_for_number(parsed, "es") or ""
    desc_en = geocoder.description_for_number(parsed, "en") or ""
    zones  = list(pntz.time_zones_for_number(parsed))

    return {
        "País/Región":              desc or desc_en or "Desconocido",
        "Región (en)":              desc_en or "N/A",
        "Código ISO País":          region or "N/A",
        "codigo_iso_pais":          region or "",   # clave interna usada por TUI
        "Zonas Horarias":           ", ".join(zones) if zones else "N/A",
    }


def get_carrier_info(parsed) -> dict:
    """Retorna información del operador."""
    if not parsed or not phonenumbers:
        return {}

    op_es = carrier.name_for_number(parsed, "es") or ""
    op_en = carrier.name_for_number(parsed, "en") or ""

    return {
        "Operador (es)": op_es or "Desconocido",
        "Operador (en)": op_en or "Desconocido",
    }


def query_ip_api(iso_code: str) -> dict:
    """Consulta ip-api.com para datos del país a partir de su código ISO."""
    if not iso_code:
        return {}
    try:
        url = f"http://ip-api.com/json/?fields=country,regionName,city,timezone,currency,isp&lang=es"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        return {
            "País (ip-api)":    data.get("country", "N/A"),
            "Región":           data.get("regionName", "N/A"),
            "Ciudad":           data.get("city", "N/A"),
            "Zona Horaria":     data.get("timezone", "N/A"),
            "Moneda":           data.get("currency", "N/A"),
        }
    except Exception:
        return {}
