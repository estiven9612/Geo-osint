#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║         PHONE OSINT v2.0 — HACKER EDITION                ║
║   TUI integrado con todos los módulos del repo           ║
╚══════════════════════════════════════════════════════════╝

Integra todos los módulos del repo:
  phoneosint.py       → análisis básico de prefijo
  hlr_lookup.py       → HLR lookup (operador actual)
  osint_cruzado.py    → Google dorks + redes sociales
  timezone_inference  → inferencia zona horaria
  batch_analysis.py   → análisis masivo
  cell_location.py    → geolocalización Cell ID
  full_pipeline.py    → pipeline completo

Extras:
  Holehe              → email en servicios (pip install holehe)
  Geoapify            → mapa región (API key gratuita)
  Claude AI           → análisis inteligente

Uso:
  python phoneosint_tui.py
  export GEOAPIFY_KEY=tu_key
  export ANTHROPIC_API_KEY=sk-ant-...
"""

import curses
import json
import os
import re
import sys
import time
import random
import threading
import urllib.request
import urllib.parse
from io import StringIO
from pathlib import Path
from datetime import datetime, timezone

# ── Agregar raíz del repo al path ────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Colores ───────────────────────────────────────────────────────────────────
C_NORMAL   = 1
C_GREEN    = 2
C_CYAN     = 3
C_RED      = 4
C_YELLOW   = 5
C_MAGENTA  = 6
C_SELECTED = 7
C_BORDER   = 8
C_HEADER   = 9
C_DIM      = 10

MATRIX_CHARS = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ01"

BANNER = [
    "  ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗ ██████╗ ███████╗██╗███╗   ██╗████████╗",
    "  ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝",
    "  ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  ██║   ██║███████╗██║██╔██╗ ██║   ██║   ",
    "  ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  ██║   ██║╚════██║██║██║╚██╗██║   ██║   ",
    "  ██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗╚██████╔╝███████║██║██║ ╚████║   ██║   ",
    "  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  ",
    "  ─────────────── O S I N T  v2.0 ── H A C K E R  E D I T I O N ──────────────────",
]

MENU_ITEMS = [
    ("[1]", "FULL PIPELINE",     "Todos los niveles en secuencia"),
    ("[2]", "PHONE LOOKUP",      "Análisis básico de prefijo + país"),
    ("[3]", "HLR LOOKUP",        "Operador actual del número"),
    ("[4]", "OSINT CRUZADO",     "Google dorks + WhatsApp + Telegram"),
    ("[5]", "TIMEZONE ANALYSIS", "Inferencia por zona horaria"),
    ("[6]", "CELL LOCATION",     "Geolocalizar por Cell ID (LAC/CID)"),
    ("[7]", "HOLEHE CHECK",      "Email → detectar servicios registrados"),
    ("[8]", "GEOAPIFY MAP",      "Mapa HTML de la región del número"),
    ("[9]", "BATCH ANALYSIS",    "Analizar múltiples números desde .txt"),
    ("[0]", "AI SUMMARY",        "Claude AI — análisis completo"),
]

REPORTS_DIR = ROOT / "osint_reports"
REPORTS_DIR.mkdir(exist_ok=True)


# ── Utilidades curses ─────────────────────────────────────────────────────────

def safe_addstr(win, y, x, text, attr=0):
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x < 0:
            return
        max_len = w - x - 1
        if max_len <= 0:
            return
        win.addstr(y, x, str(text)[:max_len], attr)
    except curses.error:
        pass


def draw_box(win, y, x, h, w, color, title=""):
    attr = curses.color_pair(color)
    try:
        win.attron(attr)
        win.addch(y,     x,     curses.ACS_ULCORNER)
        win.addch(y,     x+w-1, curses.ACS_URCORNER)
        win.addch(y+h-1, x,     curses.ACS_LLCORNER)
        win.addch(y+h-1, x+w-1, curses.ACS_LRCORNER)
        for i in range(1, w-1):
            win.addch(y,     x+i, curses.ACS_HLINE)
            win.addch(y+h-1, x+i, curses.ACS_HLINE)
        for i in range(1, h-1):
            win.addch(y+i, x,     curses.ACS_VLINE)
            win.addch(y+i, x+w-1, curses.ACS_VLINE)
        win.attroff(attr)
        if title:
            t  = f" {title} "
            tx = x + (w - len(t)) // 2
            safe_addstr(win, y, tx, t, attr | curses.A_BOLD)
    except curses.error:
        pass


def draw_header(stdscr, title="PHONE OSINT v2.0"):
    h, w = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(C_HEADER) | curses.A_BOLD)
    stdscr.addstr(0, 0, " " * (w - 1))
    safe_addstr(stdscr, 0, 2, f"[ {title} ]")
    safe_addstr(stdscr, 0, w - 12, f"[ {time.strftime('%H:%M:%S')} ]")
    stdscr.attroff(curses.color_pair(C_HEADER) | curses.A_BOLD)


def draw_footer(stdscr, hints="[Q] Quit  [↑↓] Navigate  [Enter] Select"):
    h, w = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(C_HEADER))
    stdscr.addstr(h-1, 0, " " * (w - 1))
    safe_addstr(stdscr, h-1, 2, hints)
    stdscr.attroff(curses.color_pair(C_HEADER))


def input_box(stdscr, prompt, width=58):
    h, w   = stdscr.getmaxyx()
    bh, bw = 5, min(width + 4, w - 4)
    by     = h // 2 - 2
    bx     = w // 2 - bw // 2
    popup  = curses.newwin(bh, bw, by, bx)
    draw_box(popup, 0, 0, bh, bw, C_CYAN, "INPUT")
    safe_addstr(popup, 1, 2, prompt[:bw-4], curses.color_pair(C_YELLOW))
    safe_addstr(popup, 2, 2, ">" + " " * (bw-4), curses.color_pair(C_GREEN))
    popup.refresh()
    curses.echo()
    curses.curs_set(1)
    try:
        result = popup.getstr(2, 3, bw-5).decode("utf-8", errors="ignore").strip()
    except Exception:
        result = ""
    finally:
        curses.noecho()
        curses.curs_set(0)
    return result


def show_log_screen(stdscr, title: str, lines: list,
                    hints="[Q/ESC] Back  [↑↓] Scroll  [PgUp/PgDn]  [S] Save"):
    h, w    = stdscr.getmaxyx()
    scroll  = 0
    visible = h - 4

    while True:
        stdscr.erase()
        draw_header(stdscr, title)
        draw_footer(stdscr, hints)
        draw_box(stdscr, 1, 0, h-2, w, C_BORDER)

        for i in range(visible):
            idx = scroll + i
            if idx >= len(lines):
                break
            line = str(lines[idx])
            if any(x in line for x in ["ERROR", "✗", "[!]", "error"]):
                attr = curses.color_pair(C_RED)
            elif any(x in line for x in ["⚠", "WARNING", "FOUND", "[+]", "✔"]):
                attr = curses.color_pair(C_YELLOW)
            elif any(x in line for x in ["✓", "[*]", "OK", "valid", "activo"]):
                attr = curses.color_pair(C_GREEN)
            elif any(x in line for x in ["══", "━━", "──", "===", "╔", "║", "╚"]):
                attr = curses.color_pair(C_CYAN) | curses.A_BOLD
            else:
                attr = curses.color_pair(C_GREEN)
            safe_addstr(stdscr, 2+i, 2, line[:w-4], attr)

        # Scrollbar
        if len(lines) > visible:
            pct     = scroll / max(1, len(lines) - visible)
            bar_pos = int(pct * (visible - 1))
            for i in range(visible):
                ch = "█" if i == bar_pos else "│"
                safe_addstr(stdscr, 2+i, w-2, ch, curses.color_pair(C_DIM))

        stdscr.refresh()
        key = stdscr.getch()

        if key in (ord('q'), ord('Q'), 27):
            break
        elif key == curses.KEY_UP and scroll > 0:
            scroll -= 1
        elif key == curses.KEY_DOWN and scroll < len(lines) - visible:
            scroll += 1
        elif key == curses.KEY_PPAGE:
            scroll = max(0, scroll - visible)
        elif key == curses.KEY_NPAGE:
            scroll = min(max(0, len(lines) - visible), scroll + visible)
        elif key in (ord('s'), ord('S')):
            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = REPORTS_DIR / f"report_{ts}.txt"
            out.write_text("\n".join(str(l) for l in lines))
            lines.append(f"  ✓ Guardado → {out}")
            scroll = max(0, len(lines) - visible)  # auto-scroll al final


def loading_screen(stdscr, title: str, task_fn, *args):
    result = [None]
    done   = [False]

    def run():
        result[0] = task_fn(*args)
        done[0]   = True

    t = threading.Thread(target=run, daemon=True)
    t.start()

    h, w       = stdscr.getmaxyx()
    spinners   = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    matrix_pos = [random.randint(0, h) for _ in range(w)]
    frame      = 0

    while not done[0]:
        stdscr.erase()
        draw_header(stdscr, title)

        # Matrix rain
        for col in range(min(w-1, len(matrix_pos))):
            y  = matrix_pos[col]
            ch = random.choice(MATRIX_CHARS)
            if 0 < y < h-1:
                try:
                    attr = curses.color_pair(C_GREEN)
                    if random.random() > 0.85:
                        attr |= curses.A_BOLD
                    stdscr.addstr(y, col, ch, attr)
                    if y > 1:
                        stdscr.addstr(y-1, col, ch, curses.color_pair(C_DIM))
                except curses.error:
                    pass
            matrix_pos[col] = (y + 1) % (h - 1)

        bw, bh = 44, 7
        by = h // 2 - bh // 2
        bx = w // 2 - bw // 2
        draw_box(stdscr, by, bx, bh, bw, C_CYAN, "SCANNING")
        spinner = spinners[frame % len(spinners)]
        msg     = f"{spinner}  Gathering intel... {spinner}"
        safe_addstr(stdscr, by+2, bx + (bw - len(msg)) // 2, msg,
                    curses.color_pair(C_GREEN) | curses.A_BOLD)
        dots = "." * ((frame // 3) % 4)
        safe_addstr(stdscr, by+4, bx+2, f"  Please wait{dots:<4}",
                    curses.color_pair(C_DIM))

        stdscr.refresh()
        time.sleep(0.08)
        frame += 1

    t.join()
    return result[0]


# ── Captura stdout ────────────────────────────────────────────────────────────

def capture(fn, *args, **kwargs):
    """Captura stdout de funciones existentes y devuelve lista de líneas."""
    old = sys.stdout
    sys.stdout = buf = StringIO()
    result = None
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        sys.stdout = old
        return [f"ERROR: {e}"], None
    finally:
        sys.stdout = old
    return buf.getvalue().split("\n"), result


# ── Runners ───────────────────────────────────────────────────────────────────

def run_full_pipeline(number: str, hora: str = "") -> list:
    lines = [f">>> FULL PIPELINE: {number}", ""]
    try:
        from full_pipeline import full_pipeline
        out, _ = capture(
            full_pipeline,
            phone=number,
            hora_activo=hora or None,
            save=str(REPORTS_DIR / f"full_{number.replace('+','')}.json"),
        )
        lines += out
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def run_phone_lookup(number: str) -> list:
    lines = [f">>> PHONE LOOKUP: {number}", ""]
    try:
        from phoneosint import parse_number, get_basic_info, get_geo_info, get_carrier_info, query_ip_api

        parsed = parse_number(number)
        if not parsed:
            lines.append("ERROR: Número inválido")
            return lines

        basic   = get_basic_info(parsed)
        geo     = get_geo_info(parsed)
        carrier = get_carrier_info(parsed)
        iso     = geo.get("codigo_iso_pais", "")
        country = query_ip_api(iso) if iso else {}

        lines += ["══ INFORMACIÓN BÁSICA ═══════════════════════"]
        for k, v in basic.items():
            lines.append(f"  {k:<30} {v}")

        lines += ["", "══ GEOLOCALIZACIÓN ══════════════════════════"]
        for k, v in geo.items():
            lines.append(f"  {k:<30} {v}")

        lines += ["", "══ OPERADOR ═════════════════════════════════"]
        for k, v in carrier.items():
            lines.append(f"  {k:<30} {v}")

        if country:
            lines += ["", "══ DATOS DEL PAÍS ═══════════════════════════"]
            for k, v in country.items():
                lines.append(f"  {k:<30} {v}")

        lines += [
            "",
            "══ GOOGLE DORKS ═════════════════════════════",
            f'  "{number}"',
            f'  "{number}" email OR correo',
            f'  "{number}" site:linkedin.com',
            f'  "{number}" site:facebook.com',
            f'  "{number}" whatsapp OR telegram',
            "",
            "✓ Phone lookup completo",
        ]

        out = REPORTS_DIR / f"lookup_{number.replace('+','')}.json"
        out.write_text(json.dumps(
            {"numero": number, "basic": basic, "geo": geo,
             "carrier": carrier, "country": country},
            indent=2, ensure_ascii=False, default=str
        ))
        lines.append(f"  ✓ Guardado → {out}")

    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def run_hlr(number: str) -> list:
    lines = [f">>> HLR LOOKUP: {number}", ""]
    try:
        from hlr_lookup import run_hlr as _hlr
        out, result = capture(_hlr, number)
        lines += out
        if isinstance(result, dict):
            lines += ["", "══ RESULTADO ════════════════════════════════"]
            for k, v in result.items():
                lines.append(f"  {k:<30} {v}")
        lines += ["", "✓ HLR lookup completo"]
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def run_osint_cruzado(number: str) -> list:
    lines = [f">>> OSINT CRUZADO: {number}", ""]
    try:
        from osint_cruzado import run_osint
        out, _ = capture(run_osint, number,
                         save=str(REPORTS_DIR / f"osint_{number.replace('+','')}.json"))
        lines += out

        # Búsqueda automática en DuckDuckGo
        lines += ["", "══ BÚSQUEDA AUTOMÁTICA DDG ══════════════════"]
        try:
            encoded = urllib.parse.quote(f'"{number}" email')
            url     = f"https://html.duckduckgo.com/html/?q={encoded}"
            req     = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            emails = list(set(re.findall(
                r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', html
            )))
            valid_emails = [e for e in emails if len(e) > 5 and "." in e.split("@")[-1]
                            and not e.endswith(".png") and not e.endswith(".js")]

            if valid_emails:
                lines.append("  ⚠ EMAILS ENCONTRADOS:")
                for email in valid_emails[:8]:
                    lines.append(f"    ✔ {email}")
            else:
                lines.append("  Sin emails en búsqueda automática")

        except Exception as e:
            lines.append(f"  DDG falló: {e}")

        lines += ["", "✓ OSINT cruzado completo"]
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def run_timezone(number: str, hora: str = "") -> list:
    lines = [f">>> TIMEZONE ANALYSIS: {number}", ""]
    try:
        from timezone_inference import run_timezone_analysis
        out, _ = capture(
            run_timezone_analysis,
            number,
            hora_activo=hora or None,
            save=str(REPORTS_DIR / f"tz_{number.replace('+','')}.json"),
        )
        lines += out
        lines += ["", "✓ Timezone analysis completo"]
    except Exception as e:
        lines.append(f"ERROR: {e}")
        lines.append("Instala: pip install pytz")
    return lines


def run_cell_location(mcc: str, mnc: str, lac: str, cid: str) -> list:
    lines = [f">>> CELL LOCATION MCC={mcc} MNC={mnc} LAC={lac} CID={cid}", ""]
    token = os.environ.get("UNWIRED_TOKEN", "")
    if not token:
        lines += [
            "  ⚠ UNWIRED_TOKEN no configurado",
            "  Registro gratis: https://unwiredlabs.com",
            "  Luego: export UNWIRED_TOKEN=tu_token",
            "",
            f"  Datos ingresados: MCC={mcc} MNC={mnc} LAC={lac} CID={cid}",
            "",
            "  Operadores Colombia (MCC=732):",
            "    MNC 101 = Claro",
            "    MNC 102 = Movistar",
            "    MNC 103 = Tigo",
        ]
        return lines
    try:
        import cell_location as cl
        cl.TOKEN = token
        result = cl.get_cell_location_unwired(int(mcc), int(mnc), int(lac), int(cid))
        lines += ["══ RESULTADO ════════════════════════════════"]
        for k, v in result.items():
            lines.append(f"  {k:<30} {v}")
        lines += ["", "✓ Cell location completo"]
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def run_holehe(email: str) -> list:
    lines = [f">>> HOLEHE CHECK: {email}", ""]
    try:
        import subprocess
        result = subprocess.run(
            ["holehe", email, "--only-used"],
            capture_output=True, text=True, timeout=120
        )
        output = (result.stdout + result.stderr).strip()
        if output:
            lines += ["══ SERVICIOS DETECTADOS ═════════════════════"]
            found = 0
            for line in output.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if "[+]" in line or "✔" in line:
                    found += 1
                    lines.append(f"  ✔ {line}")
                elif "[-]" not in line and "not used" not in line.lower():
                    lines.append(f"  {line}")
            lines += ["", f"  Total: {found} servicio(s) encontrado(s)", "", "✓ Holehe completo"]
        else:
            lines.append("  Sin resultados")
    except FileNotFoundError:
        lines += [
            "  ⚠ holehe no instalado",
            "  Instala: pip install holehe",
            "",
            "  Verificación manual:",
            f"  → https://haveibeenpwned.com/account/{urllib.parse.quote(email)}",
        ]
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def run_geoapify(number: str, api_key: str) -> list:
    lines = [f">>> GEOAPIFY MAP: {number}", ""]
    try:
        import phonenumbers
        from phonenumbers import geocoder

        parsed  = phonenumbers.parse(number)
        country = geocoder.description_for_number(parsed, "en")
        if not country:
            lines.append("  Sin info de país para este número")
            return lines

        encoded = urllib.parse.quote(country)
        url     = (f"https://api.geoapify.com/v1/geocode/search"
                   f"?text={encoded}&apiKey={api_key}&limit=1")

        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())

        features = data.get("features", [])
        if not features:
            lines.append(f"  Sin resultados para: {country}")
            return lines

        props  = features[0].get("properties", {})
        coords = features[0].get("geometry", {}).get("coordinates", [])

        lines += [
            "══ GEOCODIFICACIÓN ══════════════════════════",
            f"  País:       {props.get('country', 'N/A')}",
            f"  Ciudad:     {props.get('city', props.get('state', 'N/A'))}",
            f"  Estado:     {props.get('state', 'N/A')}",
            f"  Código ISO: {props.get('country_code', 'N/A').upper()}",
        ]

        if coords and len(coords) >= 2:
            lon, lat = coords[0], coords[1]
            lines += [
                f"  Latitud:    {lat}",
                f"  Longitud:   {lon}",
                "",
                "══ LINKS ════════════════════════════════════",
                f"  Google Maps:   https://maps.google.com/?q={lat},{lon}",
                f"  OpenStreetMap: https://www.openstreetmap.org/?mlat={lat}&mlon={lon}",
            ]
            html = _make_map_html(number, lat, lon, props)
            out  = REPORTS_DIR / f"map_{number.replace('+','').replace(' ','_')}.html"
            out.write_text(html)
            lines += ["", f"  ✓ Mapa HTML → {out}", "", "✓ Geoapify completo"]

    except ImportError:
        lines.append("ERROR: pip install phonenumbers")
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


def _make_map_html(number, lat, lon, props) -> str:
    country = props.get('country', 'Unknown')
    city    = props.get('city', props.get('state', ''))
    return f"""<!DOCTYPE html><html>
<head><meta charset="UTF-8"><title>PhoneOSINT — {number}</title>
<style>body{{margin:0;background:#0d1117;color:#c9d1d9;font-family:monospace}}
#map{{width:100%;height:75vh}}.info{{padding:12px;background:#161b22}}
h2{{color:#58a6ff}}.badge{{background:#1f6feb;color:#fff;padding:2px 8px;
border-radius:4px;font-size:12px;margin:2px;display:inline-block}}</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head><body><div id="map"></div>
<div class="info"><h2>📍 PhoneOSINT — {number}</h2>
<span class="badge">🌍 {country}</span>
<span class="badge">🏙 {city}</span>
<span class="badge">📍 {lat:.4f}, {lon:.4f}</span>
<p style="color:#8b949e;font-size:11px;margin-top:6px">
⚠ Región de registro del prefijo. NO es la ubicación real del dispositivo.</p>
</div><script>
var map=L.map('map').setView([{lat},{lon}],5);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
{{attribution:'© OpenStreetMap'}}).addTo(map);
L.marker([{lat},{lon}]).addTo(map)
.bindPopup('<b>{number}</b><br>{country} — {city}').openPopup();
</script></body></html>"""


def run_batch(filepath: str) -> list:
    lines = [f">>> BATCH ANALYSIS: {filepath}", ""]
    try:
        from batch_analysis import analyze_batch
        out_path = str(REPORTS_DIR / f"batch_{int(time.time())}.json")
        out, _   = capture(analyze_batch, filepath, out_path)
        lines += out
        lines += ["", f"✓ Batch completo → {out_path}"]
    except Exception as e:
        lines.append(f"ERROR: {e}")
        lines.append("Instala: pip install phonenumbers")
    return lines


def run_ai_summary(number: str, api_key: str) -> list:
    lines = [f">>> AI SUMMARY: {number}", ""]
    if not api_key:
        lines += ["ERROR: ANTHROPIC_API_KEY no configurado",
                  "Setea: export ANTHROPIC_API_KEY=sk-ant-..."]
        return lines
    try:
        from phoneosint import parse_number, get_basic_info, get_geo_info, get_carrier_info
        from phonenumbers import timezone as pntz

        parsed  = parse_number(number)
        basic   = get_basic_info(parsed)   if parsed else {}
        geo     = get_geo_info(parsed)     if parsed else {}
        carrier = get_carrier_info(parsed) if parsed else {}
        zones   = list(pntz.time_zones_for_number(parsed)) if parsed else []

        prompt = f"""Eres un analista OSINT experto. Analiza este número telefónico.

NÚMERO: {number}
VÁLIDO: {basic.get('valido', '?')}
TIPO: {basic.get('tipo', '?')}
REGIÓN: {geo.get('region_aproximada', '?')}
ISO: {geo.get('codigo_iso_pais', '?')}
OPERADOR: {carrier.get('operador', '?')}
ZONAS HORARIAS: {', '.join(zones)}

Genera un reporte OSINT profesional con:
1. EVALUACIÓN DE RIESGO — ¿Sospechoso? (spam/scam/legítimo)
2. PERFIL GEOGRÁFICO — Análisis de la región
3. INTELIGENCIA DEL OPERADOR — Qué revela el carrier
4. TOP 5 PASOS OSINT — Próximos pasos de investigación
5. MEJORES DORKS — 3 búsquedas más efectivas
6. NIVEL DE CONFIANZA — Qué tan confiable es el análisis

Responde en español. Sé conciso y técnico."""

        payload = json.dumps({
            "model":      "claude-sonnet-4-20250514",
            "max_tokens": 1200,
            "messages":   [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
            },
        )

        lines += ["  [*] Enviando a Claude API...", "", "═" * 55]
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())

        text = "".join(b.get("text","") for b in data.get("content",[])
                       if b.get("type") == "text")
        lines += text.split("\n")
        lines += ["", f"  Tokens: {data.get('usage', {})}", "", "✓ AI Summary completo"]

        out = REPORTS_DIR / f"ai_{number.replace('+','').replace(' ','_')}.txt"
        out.write_text("\n".join(str(l) for l in lines))
        lines.append(f"  ✓ Guardado → {out}")

    except Exception as e:
        lines.append(f"ERROR: {e}")
    return lines


# ── Manejo de selecciones ─────────────────────────────────────────────────────

def handle_selection(stdscr, idx: int):
    geo_key = os.environ.get("GEOAPIFY_KEY", "")
    ai_key  = os.environ.get("ANTHROPIC_API_KEY", "")

    if idx == 0:  # Full pipeline
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if not number:
            return
        hora = input_box(stdscr, "Hora última actividad UTC HH:MM (Enter=omitir):", width=45)
        lines = loading_screen(stdscr, "FULL PIPELINE", run_full_pipeline, number, hora)
        show_log_screen(stdscr, "FULL PIPELINE", lines)

    elif idx == 1:  # Phone lookup
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if number:
            lines = loading_screen(stdscr, "PHONE LOOKUP", run_phone_lookup, number)
            show_log_screen(stdscr, "PHONE LOOKUP", lines)

    elif idx == 2:  # HLR
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if number:
            lines = loading_screen(stdscr, "HLR LOOKUP", run_hlr, number)
            show_log_screen(stdscr, "HLR LOOKUP", lines)

    elif idx == 3:  # OSINT cruzado
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if number:
            lines = loading_screen(stdscr, "OSINT CRUZADO", run_osint_cruzado, number)
            show_log_screen(stdscr, "OSINT CRUZADO", lines)

    elif idx == 4:  # Timezone
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if not number:
            return
        hora = input_box(stdscr, "Hora actividad UTC HH:MM (Enter=omitir):", width=42)
        lines = loading_screen(stdscr, "TIMEZONE ANALYSIS", run_timezone, number, hora)
        show_log_screen(stdscr, "TIMEZONE ANALYSIS", lines)

    elif idx == 5:  # Cell location
        mcc = input_box(stdscr, "MCC (ej: 732 Colombia):", width=25) or "732"
        mnc = input_box(stdscr, "MNC (ej: 101=Claro 102=Movistar 103=Tigo):", width=42) or "101"
        lac = input_box(stdscr, "LAC:", width=20)
        cid = input_box(stdscr, "CID:", width=20)
        if lac and cid:
            lines = loading_screen(stdscr, "CELL LOCATION",
                                   run_cell_location, mcc, mnc, lac, cid)
            show_log_screen(stdscr, "CELL LOCATION", lines)

    elif idx == 6:  # Holehe
        email = input_box(stdscr, "Email a verificar:", width=55)
        if email:
            lines = loading_screen(stdscr, "HOLEHE CHECK", run_holehe, email)
            show_log_screen(stdscr, "HOLEHE CHECK", lines)

    elif idx == 7:  # Geoapify
        if not geo_key:
            geo_key = input_box(stdscr, "Geoapify API Key (gratis en geoapify.com):", width=60)
        if not geo_key:
            show_log_screen(stdscr, "ERROR", [
                "  ERROR: Se necesita Geoapify API key",
                "  1. Ve a https://geoapify.com",
                "  2. Regístrate gratis (3000 req/día)",
                "  3. export GEOAPIFY_KEY=tu_key",
            ])
            return
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if number:
            lines = loading_screen(stdscr, "GEOAPIFY MAP", run_geoapify, number, geo_key)
            show_log_screen(stdscr, "GEOAPIFY MAP", lines)

    elif idx == 8:  # Batch
        filepath = input_box(stdscr, "Ruta archivo .txt con números (uno por línea):", width=60)
        if filepath:
            lines = loading_screen(stdscr, "BATCH ANALYSIS", run_batch, filepath)
            show_log_screen(stdscr, "BATCH ANALYSIS", lines)

    elif idx == 9:  # AI Summary
        if not ai_key:
            ai_key = input_box(stdscr, "Anthropic API Key:", width=65)
        number = input_box(stdscr, "Número (ej: +573001234567):", width=52)
        if number:
            lines = loading_screen(stdscr, "AI SUMMARY", run_ai_summary, number, ai_key)
            show_log_screen(stdscr, "AI SUMMARY", lines)


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_NORMAL,   curses.COLOR_WHITE,   -1)
    curses.init_pair(C_GREEN,    curses.COLOR_GREEN,   -1)
    curses.init_pair(C_CYAN,     curses.COLOR_CYAN,    -1)
    curses.init_pair(C_RED,      curses.COLOR_RED,     -1)
    curses.init_pair(C_YELLOW,   curses.COLOR_YELLOW,  -1)
    curses.init_pair(C_MAGENTA,  curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_SELECTED, curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(C_BORDER,   curses.COLOR_WHITE,   -1)
    curses.init_pair(C_HEADER,   curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(C_DIM,      curses.COLOR_GREEN,   -1)

    curses.curs_set(0)
    curses.noecho()
    stdscr.keypad(True)

    selected   = 0
    h, w       = stdscr.getmaxyx()
    matrix_pos = [random.randint(0, h) for _ in range(w)]

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        draw_header(stdscr)
        draw_footer(stdscr, "[↑↓] Navigate  [Enter/0-9] Select  [Q] Quit")

        # Banner
        banner_y = 1
        for i, line in enumerate(BANNER):
            color = C_GREEN if i < len(BANNER)-1 else C_CYAN
            attr  = curses.color_pair(color)
            if i < len(BANNER)-1:
                attr |= curses.A_BOLD
            safe_addstr(stdscr, banner_y+i, max(0, (w-len(line))//2), line, attr)

        menu_y = banner_y + len(BANNER) + 1
        menu_w = min(72, w-4)
        menu_x = (w - menu_w) // 2
        menu_h = len(MENU_ITEMS) + 2
        draw_box(stdscr, menu_y, menu_x, menu_h, menu_w, C_BORDER, "[ SELECT MODULE ]")

        for i, (key, name, desc) in enumerate(MENU_ITEMS):
            is_sel = (i == selected)
            y = menu_y + 1 + i
            x = menu_x + 2
            if is_sel:
                attr = curses.color_pair(C_SELECTED) | curses.A_BOLD
                safe_addstr(stdscr, y, menu_x+1, " " * (menu_w-2), attr)
                safe_addstr(stdscr, y, x, f"{key} {name:<22} {desc}", attr)
            else:
                safe_addstr(stdscr, y, x,    key,           curses.color_pair(C_YELLOW) | curses.A_BOLD)
                safe_addstr(stdscr, y, x+4,  f"{name:<22}", curses.color_pair(C_GREEN)  | curses.A_BOLD)
                safe_addstr(stdscr, y, x+27, desc,          curses.color_pair(C_DIM))

        # Status bar
        sy     = menu_y + menu_h + 1
        geo_ok = bool(os.environ.get("GEOAPIFY_KEY"))
        ai_ok  = bool(os.environ.get("ANTHROPIC_API_KEY"))
        uw_ok  = bool(os.environ.get("UNWIRED_TOKEN"))
        safe_addstr(stdscr, sy, menu_x,
            f"  GEOAPIFY: {'✓' if geo_ok else '✗'}  "
            f"CLAUDE_API: {'✓' if ai_ok else '✗'}  "
            f"UNWIRED: {'✓' if uw_ok else '✗'}  "
            f"Reports: {REPORTS_DIR}",
            curses.color_pair(C_DIM))

        stdscr.refresh()
        stdscr.timeout(100)
        key = stdscr.getch()
        stdscr.timeout(-1)

        if key == curses.KEY_UP:
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_ENTER, 10, 13):
            handle_selection(stdscr, selected)
        elif key in range(ord('0'), ord('9')+1):
            idx = (key - ord('0') - 1) % len(MENU_ITEMS)
            handle_selection(stdscr, idx)
        elif key in (ord('q'), ord('Q')):
            break


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    curses.wrapper(main_menu)


if __name__ == "__main__":
    main()
