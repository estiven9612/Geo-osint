"""
osint_cruzado.py — OSINT Cruzado: Dorks + Redes Sociales
Genera dorks de Google, busca en DuckDuckGo y redes sociales.
Usado por: phoneosint_tui.py (módulo [3])
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime


def _ddg_search(query: str, timeout: int = 10) -> list:
    """Busca en DuckDuckGo HTML y retorna lista de resultados."""
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Extraer links y snippets
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<', html)
        snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)<', html)

        for i, (link, title) in enumerate(links[:8]):
            results.append({
                "title":   title.strip(),
                "url":     link.strip(),
                "snippet": snippets[i].strip() if i < len(snippets) else "",
            })
    except Exception as e:
        results.append({"error": str(e)})
    return results


def _generate_dorks(number: str) -> list:
    """Genera lista de Google dorks para el número."""
    clean = number.replace("+", "").replace(" ", "").replace("-", "")
    intl  = number if number.startswith("+") else f"+{clean}"

    dorks = [
        f'"{number}"',
        f'"{intl}"',
        f'"{number}" site:facebook.com',
        f'"{number}" site:instagram.com',
        f'"{number}" site:twitter.com',
        f'"{number}" site:linkedin.com',
        f'"{number}" site:truecaller.com',
        f'"{number}" site:whitepages.com',
        f'"{number}" filetype:pdf',
        f'"{number}" intext:whatsapp',
        f'"{number}" email',
        f'"{clean}" telefono',
    ]
    return dorks


def _check_truecaller(number: str) -> dict:
    """Intenta obtener info de Truecaller (sin auth — datos limitados)."""
    try:
        clean = number.replace("+", "").replace(" ", "")
        url = f"https://search5-noneu.truecaller.com/v2/search?q={clean}&countryCode=CO&type=4&locAddr=&encoding=json"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Authorization": "Bearer ANONYMOUS"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        if data.get("data"):
            d = data["data"][0]
            name = d.get("name", "")
            if name:
                return {"Nombre en Truecaller": name, "Score": d.get("score", "N/A")}
    except Exception:
        pass
    return {}


def run_osint(number: str, save: str = None) -> dict:
    """
    Ejecuta OSINT cruzado completo para el número.
    Retorna dict con dorks, resultados DDG y redes sociales.
    """
    print(f"[*] OSINT Cruzado: {number}")
    report = {
        "numero":    number,
        "timestamp": datetime.now().isoformat(),
        "dorks":     [],
        "ddg":       {},
        "truecaller": {},
        "redes":     {},
    }

    # 1. Generar dorks
    dorks = _generate_dorks(number)
    report["dorks"] = dorks
    print(f"[+] {len(dorks)} dorks generados")
    for d in dorks:
        print(f"  → {d}")

    # 2. Búsqueda principal en DDG
    print("\n[*] Buscando en DuckDuckGo...")
    main_results = _ddg_search(f'"{number}"')
    report["ddg"]["principal"] = main_results
    if main_results and "error" not in main_results[0]:
        print(f"[+] {len(main_results)} resultados DDG")
        for r in main_results[:5]:
            print(f"  • {r.get('title', '')} — {r.get('url', '')}")
    else:
        print("  [-] Sin resultados en DDG")

    # 3. Búsqueda email
    print("\n[*] Buscando posibles emails...")
    email_results = _ddg_search(f'"{number}" email OR correo')
    report["ddg"]["email"] = email_results
    emails_found = []
    for r in email_results:
        snippet = r.get("snippet", "") + r.get("url", "")
        found = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', snippet)
        emails_found.extend(found)
    emails_found = list(set([e for e in emails_found if len(e) > 5 and "." in e.split("@")[-1]
                              and not e.endswith((".png", ".js", ".css"))]))
    if emails_found:
        print(f"[+] Posibles emails: {', '.join(emails_found[:5])}")
        report["ddg"]["emails_detectados"] = emails_found

    # 4. Truecaller
    print("\n[*] Consultando Truecaller...")
    tc = _check_truecaller(number)
    report["truecaller"] = tc
    if tc:
        for k, v in tc.items():
            print(f"  {k}: {v}")
    else:
        print("  [-] Sin resultados en Truecaller")

    # 5. Redes sociales (búsqueda DDG específica)
    redes = ["facebook", "instagram", "twitter", "linkedin"]
    for red in redes:
        print(f"\n[*] Buscando en {red.capitalize()}...")
        res = _ddg_search(f'"{number}" site:{red}.com', timeout=8)
        report["redes"][red] = res
        if res and "error" not in res[0]:
            print(f"  [+] {len(res)} resultados en {red.capitalize()}")
        else:
            print(f"  [-] Sin resultados en {red.capitalize()}")

    # 6. Guardar reporte
    if save:
        try:
            import pathlib
            pathlib.Path(save).parent.mkdir(parents=True, exist_ok=True)
            with open(save, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n[+] Reporte guardado: {save}")
        except Exception as e:
            print(f"  [-] Error guardando: {e}")

    return report
