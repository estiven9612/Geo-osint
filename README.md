# 📡 PhoneOSINT v2.0 — Hacker Edition

```
██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗ ██████╗ ███████╗██╗███╗   ██╗████████╗
██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  ██║   ██║███████╗██║██╔██╗ ██║   ██║   
██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  ██║   ██║╚════██║██║██║╚██╗██║   ██║   
██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗╚██████╔╝███████║██║██║ ╚████║   ██║   
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  
──────────────── O S I N T  v2.0 ── H A C K E R  E D I T I O N ─────────────────
```

> Herramienta OSINT para análisis de números telefónicos con interfaz TUI estilo hacker. Integra múltiples módulos de inteligencia, geolocalización, HLR lookup, búsqueda cruzada y análisis con IA.

---

## 📋 Módulos disponibles

| # | Módulo | Descripción |
|---|--------|-------------|
| 1 | **FULL PIPELINE** | Ejecuta todos los niveles de análisis en secuencia |
| 2 | **PHONE LOOKUP** | Análisis básico de prefijo, país y operador |
| 3 | **HLR LOOKUP** | Consulta el operador actual real del número |
| 4 | **OSINT CRUZADO** | Google dorks + búsqueda en WhatsApp y Telegram |
| 5 | **TIMEZONE ANALYSIS** | Inferencia de zona horaria por prefijo |
| 6 | **CELL LOCATION** | Geolocalización por Cell ID (MCC/MNC/LAC/CID) |
| 7 | **HOLEHE CHECK** | Detecta en qué servicios está registrado un email |
| 8 | **GEOAPIFY MAP** | Genera un mapa HTML interactivo de la región del número |
| 9 | **BATCH ANALYSIS** | Analiza múltiples números desde un archivo `.txt` |
| 0 | **AI SUMMARY** | Análisis inteligente completo con Claude AI |

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/phoneosint.git
cd phoneosint
```

### 2. Instalar dependencias

```bash
# Obligatorias
pip install phonenumbers --break-system-packages

# Opcionales (según módulos que uses)
pip install holehe pytz --break-system-packages
```

### 3. Configurar variables de entorno

```bash
# Claude AI — módulo AI SUMMARY
export ANTHROPIC_API_KEY="sk-ant-..."

# Geoapify — módulo GEOAPIFY MAP (gratis en geoapify.com, 3000 req/día)
export GEOAPIFY_KEY="tu_key_aqui"

# Unwired Labs — módulo CELL LOCATION (gratis en unwiredlabs.com)
export UNWIRED_TOKEN="tu_token_aqui"
```

> 💡 Para que las variables sean permanentes, agrégalas a tu `~/.bashrc` o `~/.zshrc` y ejecuta `source ~/.bashrc`.

---

## 🚀 Uso

```bash
python phoneosint_tui.py
```

### Navegación en la TUI

| Tecla | Acción |
|-------|--------|
| `↑` / `↓` | Navegar el menú |
| `Enter` | Seleccionar módulo |
| `1`–`9`, `0` | Acceso directo al módulo |
| `S` | Guardar resultado actual como `.txt` |
| `↑` / `↓` / `PgUp` / `PgDn` | Scroll en resultados |
| `Q` / `ESC` | Volver / Salir |

---

## 🗂️ Estructura del proyecto

```
phoneosint/
├── phoneosint_tui.py     # TUI principal (este archivo)
├── phoneosint.py         # Análisis básico de prefijo
├── hlr_lookup.py         # HLR lookup — operador actual
├── osint_cruzado.py      # Google dorks + redes sociales
├── full_pipeline.py      # Pipeline completo encadenado
├── batch_analysis.py     # Análisis masivo desde archivo
├── cell_location.py      # Geolocalización por Cell ID
└── osint_reports/        # Reportes generados (JSON, HTML, TXT)
```

---

## 🔑 APIs requeridas

| API | Módulo | Costo | Registro |
|-----|--------|-------|----------|
| [Anthropic Claude](https://console.anthropic.com) | AI SUMMARY | De pago | console.anthropic.com |
| [Geoapify](https://geoapify.com) | GEOAPIFY MAP | Gratis (3000/día) | geoapify.com |
| [Unwired Labs](https://unwiredlabs.com) | CELL LOCATION | Gratis (100/día) | unwiredlabs.com |

---

## 📄 Reportes

Todos los resultados se guardan automáticamente en la carpeta `osint_reports/`:

- `lookup_NUMERO.json` — Resultado de Phone Lookup
- `osint_NUMERO.json` — Resultado de OSINT Cruzado
- `full_NUMERO.json` — Resultado de Full Pipeline
- `map_NUMERO.html` — Mapa interactivo (Geoapify)
- `ai_NUMERO.txt` — Análisis de Claude AI
- `batch_TIMESTAMP.json` — Análisis masivo
- `report_TIMESTAMP.txt` — Guardado manual con `[S]`

---

## ⚠️ Disclaimer

Esta herramienta es para uso **educativo y de investigación legal** únicamente. El autor no se hace responsable del uso indebido. Úsala solo sobre números de tu propiedad o con autorización expresa. Consulta las leyes de tu país antes de realizar cualquier tipo de OSINT.

---

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
