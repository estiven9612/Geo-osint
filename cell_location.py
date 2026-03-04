"""
cell_location.py — Geolocalización por Cell ID (MCC/MNC/LAC/CID)
Usa Unwired Labs API (TOKEN requerido).
Usado por: phoneosint_tui.py (módulo [6])
"""

import json
import urllib.request

# Token configurable desde el TUI (se sobreescribe con cl.TOKEN = ...)
TOKEN = ""


def get_cell_location_unwired(mcc: int, mnc: int, lac: int, cid: int) -> dict:
    """
    Consulta Unwired Labs para obtener la ubicación de una celda.
    Args:
        mcc: Mobile Country Code
        mnc: Mobile Network Code
        lac: Location Area Code
        cid: Cell ID
    Returns:
        dict con lat, lon, accuracy, operador, país
    """
    if not TOKEN:
        return {"Error": "UNWIRED_TOKEN no configurado. Setea: export UNWIRED_TOKEN=tu_token"}

    print(f"[*] Cell Location: MCC={mcc} MNC={mnc} LAC={lac} CID={cid}")

    payload = json.dumps({
        "token":  TOKEN,
        "radio":  "gsm",
        "mcc":    mcc,
        "mnc":    mnc,
        "cells": [
            {
                "lac": lac,
                "cid": cid,
            }
        ],
        "address": 1,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://us1.unwiredlabs.com/v2/process.php",
            data=payload,
            headers={
                "Content-Type":  "application/json",
                "User-Agent":    "PhoneOSINT/2.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") == "ok":
            result = {
                "Latitud":       str(data.get("lat", "N/A")),
                "Longitud":      str(data.get("lon", "N/A")),
                "Precisión (m)": str(data.get("accuracy", "N/A")),
                "Balance":       str(data.get("balance", "N/A")),
            }
            # Dirección si está disponible
            address = data.get("address", {})
            if address:
                result["País"]      = address.get("country", "N/A")
                result["Ciudad"]    = address.get("city", "N/A") or address.get("county", "N/A")
                result["Estado"]    = address.get("state", "N/A")
                result["Dirección"] = address.get("display_name", "N/A")

            print(f"[+] Ubicación: {result.get('Latitud')}, {result.get('Longitud')}")
            print(f"    Precisión: {result.get('Precisión (m)')} metros")
            return result
        else:
            msg = data.get("message", "Error desconocido")
            print(f"  [-] Error Unwired Labs: {msg}")
            return {"Error": msg, "Status": data.get("status", "error")}

    except Exception as e:
        print(f"  [-] Excepción: {e}")
        return {"Error": str(e)}


def get_cell_location_opencellid(mcc: int, mnc: int, lac: int, cid: int) -> dict:
    """
    Alternativa usando OpenCelliD (requiere API key gratuita).
    https://opencellid.org/
    """
    print(f"[*] OpenCelliD: MCC={mcc} MNC={mnc} LAC={lac} CID={cid}")
    try:
        import os
        key = os.environ.get("OPENCELLID_KEY", "")
        if not key:
            return {"Error": "OPENCELLID_KEY no configurado"}

        url = (
            f"https://opencellid.org/cell/get?key={key}"
            f"&mcc={mcc}&mnc={mnc}&lac={lac}&cellid={cid}&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "PhoneOSINT/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("lat"):
            return {
                "Latitud":       str(data.get("lat")),
                "Longitud":      str(data.get("lon")),
                "Precisión (m)": str(data.get("range", "N/A")),
                "Fuente":        "OpenCelliD",
            }
        return {"Error": str(data)}
    except Exception as e:
        return {"Error": str(e)}
