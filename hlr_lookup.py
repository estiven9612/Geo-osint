"""
hlr_lookup.py — HLR Lookup (Home Location Register)
Intenta determinar el operador actual / portabilidad del número.
Usado por: phoneosint_tui.py (módulo [2])
"""

import json
import urllib.request
import urllib.parse


def run_hlr(number: str) -> dict:
    """
    Realiza HLR lookup usando APIs gratuitas.
    Retorna dict con info del operador actual.
    """
    print(f"[*] HLR Lookup: {number}")
    result = {}

    # --- Método 1: hlr-lookups.com (sin auth, datos limitados) ---
    try:
        encoded = urllib.parse.quote(number)
        url = f"https://api.hlr-lookups.com/json?msisdn={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("success"):
            result["Operador Actual"]   = data.get("operator", "N/A")
            result["País"]              = data.get("country_name", "N/A")
            result["MCC"]               = data.get("mcc", "N/A")
            result["MNC"]               = data.get("mnc", "N/A")
            result["Portado"]           = "Sí" if data.get("ported") else "No"
            result["Estado"]            = data.get("status", "N/A")
            result["Roaming"]           = "Sí" if data.get("roaming") else "No"
            print(f"[+] HLR via hlr-lookups.com: {result.get('Operador Actual', 'N/A')}")
            return result
    except Exception as e:
        print(f"  [-] hlr-lookups.com falló: {e}")

    # --- Método 2: apilayer numverify (sin key, datos básicos) ---
    try:
        encoded = urllib.parse.quote(number.lstrip("+"))
        url = f"http://apilayer.net/api/validate?number={encoded}&format=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("valid"):
            result["Operador Actual"]   = data.get("carrier", "N/A")
            result["País"]              = data.get("country_name", "N/A")
            result["Código País"]       = data.get("country_code", "N/A")
            result["Tipo de Línea"]     = data.get("line_type", "N/A")
            result["Número Local"]      = data.get("local_format", "N/A")
            result["Número Intl"]       = data.get("international_format", "N/A")
            print(f"[+] HLR via numverify: {result.get('Operador Actual', 'N/A')}")
            return result
    except Exception as e:
        print(f"  [-] numverify falló: {e}")

    # --- Método 3: phonenumbers local (sin red) ---
    try:
        import phonenumbers
        from phonenumbers import carrier as pn_carrier, geocoder
        parsed = phonenumbers.parse(number, None)
        op = pn_carrier.name_for_number(parsed, "es") or pn_carrier.name_for_number(parsed, "en")
        geo = geocoder.description_for_number(parsed, "es")
        result["Operador (local)"]  = op or "Desconocido"
        result["País (local)"]      = geo or "Desconocido"
        result["Nota"]              = "Datos locales (sin consulta de red)"
        print(f"[+] HLR via phonenumbers local: {op or 'N/A'}")
    except Exception as e:
        result["Error"] = str(e)
        print(f"  [-] phonenumbers falló: {e}")

    return result
