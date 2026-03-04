"""
hlr_lookup.py — HLR Lookup (Home Location Register)
Intenta determinar el operador actual, portabilidad y nombre del dueño.
Usado por: phoneosint_tui.py (módulo [2])
"""

import json
import urllib.request
import urllib.parse


def _numlookup(number: str) -> dict:
    """
    Consulta NumLookup.com — retorna nombre del dueño si está disponible.
    Gratuito, sin API key.
    """
    try:
        clean = number.lstrip("+").replace(" ", "").replace("-", "")
        url = f"https://www.numlookup.com/json/number/{clean}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Accept":     "application/json",
            "Referer":    "https://www.numlookup.com/",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        result = {}
        name = data.get("name") or data.get("caller_name") or data.get("owner")
        if name and name.lower() not in ("unknown", "n/a", "", "none"):
            result["Nombre (NumLookup)"] = name
        carrier = data.get("carrier") or data.get("operator")
        if carrier:
            result["Operador (NumLookup)"] = carrier
        line_type = data.get("line_type") or data.get("type")
        if line_type:
            result["Tipo (NumLookup)"] = line_type
        spam = data.get("spam_score") or data.get("fraud_score")
        if spam is not None:
            result["Spam Score"] = str(spam)
        if result:
            print(f"[+] NumLookup: {result}")
        else:
            print("  [-] NumLookup: sin datos de nombre")
        return result
    except Exception as e:
        print(f"  [-] NumLookup falló: {e}")
        return {}


def _calleridtest(number: str) -> dict:
    """
    Consulta CallerIDTest.com — base de datos de nombres de llamadas.
    """
    try:
        clean = urllib.parse.quote(number)
        url = f"https://www.calleridtest.com/api/lookup?number={clean}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept":     "application/json",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        result = {}
        name = data.get("name") or data.get("caller_name")
        if name and name.lower() not in ("unknown", "unavailable", ""):
            result["Nombre (CallerID)"] = name
            print(f"[+] CallerIDTest: {name}")
        return result
    except Exception as e:
        print(f"  [-] CallerIDTest falló: {e}")
        return {}


def _truecaller_search(number: str) -> dict:
    """
    Búsqueda pública en Truecaller (sin auth — resultados limitados).
    """
    try:
        clean = number.replace("+", "").replace(" ", "")
        url = (
            f"https://search5-noneu.truecaller.com/v2/search"
            f"?q={clean}&countryCode=CO&type=4&locAddr=&encoding=json"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent":    "Mozilla/5.0",
            "Authorization": "Bearer ANONYMOUS",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        if data.get("data"):
            d = data["data"][0]
            name = d.get("name", "")
            if name:
                print(f"[+] Truecaller: {name}")
                return {
                    "Nombre (Truecaller)": name,
                    "Score Truecaller":    str(d.get("score", "N/A")),
                }
    except Exception as e:
        print(f"  [-] Truecaller falló: {e}")
    return {}


def run_hlr(number: str) -> dict:
    """
    Realiza HLR lookup + búsqueda de nombre del dueño.
    Retorna dict con operador, país y nombre si se encontró.
    """
    print(f"[*] HLR Lookup: {number}")
    result = {}

    # --- Método 1: hlr-lookups.com ---
    try:
        encoded = urllib.parse.quote(number)
        url = f"https://api.hlr-lookups.com/json?msisdn={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("success"):
            result["Operador Actual"] = data.get("operator", "N/A")
            result["País"]            = data.get("country_name", "N/A")
            result["MCC"]             = data.get("mcc", "N/A")
            result["MNC"]             = data.get("mnc", "N/A")
            result["Portado"]         = "Sí" if data.get("ported") else "No"
            result["Roaming"]         = "Sí" if data.get("roaming") else "No"
            print(f"[+] HLR via hlr-lookups.com: {result.get('Operador Actual')}")
    except Exception:
        pass  # silencioso — falla esperada sin API key

    # --- Método 2: numverify ---
    if not result:
        try:
            encoded = urllib.parse.quote(number.lstrip("+"))
            url = f"http://apilayer.net/api/validate?number={encoded}&format=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data.get("valid"):
                result["Operador Actual"] = data.get("carrier", "N/A")
                result["País"]            = data.get("country_name", "N/A")
                result["Tipo de Línea"]   = data.get("line_type", "N/A")
                print(f"[+] HLR via numverify: {result.get('Operador Actual')}")
        except Exception:
            pass

    # --- Método 3: phonenumbers local (siempre disponible) ---
    if not result:
        try:
            import phonenumbers
            from phonenumbers import carrier as pn_carrier, geocoder
            parsed = phonenumbers.parse(number, None)
            op  = pn_carrier.name_for_number(parsed, "es") or pn_carrier.name_for_number(parsed, "en")
            geo = geocoder.description_for_number(parsed, "es")
            result["Operador (local)"] = op or "Desconocido"
            result["País (local)"]     = geo or "Desconocido"
            result["Nota"]             = "Datos locales (sin consulta de red)"
            print(f"[+] HLR via phonenumbers local: {op or 'N/A'}")
        except Exception as e:
            result["Error"] = str(e)

    # --- Búsqueda de nombre del dueño ---
    print("\n[*] Buscando nombre del dueño...")

    # NumLookup
    nl = _numlookup(number)
    result.update(nl)

    # Truecaller
    tc = _truecaller_search(number)
    result.update(tc)

    # CallerIDTest
    cid = _calleridtest(number)
    result.update(cid)

    # Resumen de nombre encontrado
    nombre = (
        result.get("Nombre (Truecaller)") or
        result.get("Nombre (NumLookup)") or
        result.get("Nombre (CallerID)") or
        "No encontrado"
    )
    result["══ Nombre identificado"] = nombre

    return result
