#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║         PHONE OSINT v2.0 — INSTALLER                    ║
# ║         Kali Linux / Debian / Ubuntu                    ║
# ╚══════════════════════════════════════════════════════════╝

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_banner() {
echo -e "${GREEN}"
cat << 'EOF'
  ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗ ██████╗ ███████╗██╗███╗   ██╗████████╗
  ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
  ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  ██║   ██║███████╗██║██╔██╗ ██║   ██║
  ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  ██║   ██║╚════██║██║██║╚██╗██║   ██║
  ██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗╚██████╔╝███████║██║██║ ╚████║   ██║
  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
  ──────────────── INSTALLER v2.0 ── KALI EDITION ──────────────────────────────────
EOF
echo -e "${NC}"
}

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
info() { echo -e "  ${CYAN}[*]${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

# ── 1. Banner ─────────────────────────────────────────────────────────────────
print_banner
echo -e "${CYAN}  Iniciando instalación...${NC}\n"

# ── 2. Python ─────────────────────────────────────────────────────────────────
info "Verificando Python 3..."
if ! command -v python3 &>/dev/null; then
    fail "Python 3 no encontrado. Instala con: sudo apt install python3"
    exit 1
fi
PYVER=$(python3 --version 2>&1)
ok "Encontrado: $PYVER"

# ── 3. pip ────────────────────────────────────────────────────────────────────
info "Verificando pip..."
if ! command -v pip &>/dev/null && ! command -v pip3 &>/dev/null; then
    warn "pip no encontrado. Instalando..."
    sudo apt-get install -y python3-pip
fi
ok "pip disponible"

# ── 4. Dependencias Python ────────────────────────────────────────────────────
echo ""
info "Instalando dependencias Python..."

PACKAGES=("phonenumbers" "pytz")
for pkg in "${PACKAGES[@]}"; do
    info "Instalando $pkg..."
    pip install "$pkg" --break-system-packages -q && ok "$pkg instalado" || warn "$pkg falló (puede que ya esté instalado)"
done

# ── 5. Holehe (opcional) ──────────────────────────────────────────────────────
echo ""
info "Instalando holehe (módulo email check)..."
pip install holehe --break-system-packages -q && ok "holehe instalado" || warn "holehe falló — el módulo [7] no estará disponible"

# ── 6. Carpeta de reportes ────────────────────────────────────────────────────
echo ""
info "Creando carpeta de reportes..."
mkdir -p osint_reports
ok "osint_reports/ lista"

# ── 7. Variables de entorno ───────────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}  ║        CONFIGURACIÓN DE API KEYS         ║${NC}"
echo -e "${CYAN}  ╚══════════════════════════════════════════╝${NC}"
echo ""

SHELL_RC="$HOME/.bashrc"
[[ "$SHELL" == *"zsh"* ]] && SHELL_RC="$HOME/.zshrc"

configure_key() {
    local VAR_NAME=$1
    local LABEL=$2
    local URL=$3

    if grep -q "export $VAR_NAME=" "$SHELL_RC" 2>/dev/null; then
        warn "$LABEL ya configurada en $SHELL_RC — omitiendo"
        return
    fi

    echo -e "  ${YELLOW}$LABEL${NC}"
    echo -e "  Regístrate gratis en: ${CYAN}$URL${NC}"
    read -rp "  Pega tu key (Enter para omitir): " KEY
    if [[ -n "$KEY" ]]; then
        echo "" >> "$SHELL_RC"
        echo "# PhoneOSINT — $LABEL" >> "$SHELL_RC"
        echo "export $VAR_NAME=\"$KEY\"" >> "$SHELL_RC"
        export "$VAR_NAME"="$KEY"
        ok "$LABEL guardada en $SHELL_RC"
    else
        warn "$LABEL omitida — puedes agregarla después con:"
        echo "       export $VAR_NAME=\"tu_key\""
    fi
    echo ""
}

configure_key "ANTHROPIC_API_KEY" "Claude AI API Key"   "https://console.anthropic.com"
configure_key "GEOAPIFY_KEY"      "Geoapify API Key"    "https://geoapify.com  (gratis, 3000 req/día)"
configure_key "UNWIRED_TOKEN"     "Unwired Labs Token"  "https://unwiredlabs.com  (gratis, 100 req/día)"

# ── 8. Permisos de ejecución ──────────────────────────────────────────────────
info "Configurando permisos..."
chmod +x phoneosint_tui.py 2>/dev/null && ok "phoneosint_tui.py ejecutable" || true

# ── 9. Resumen final ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║         INSTALACIÓN COMPLETA ✓           ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Para iniciar:"
echo -e "  ${CYAN}source $SHELL_RC${NC}"
echo -e "  ${CYAN}python3 phoneosint_tui.py${NC}"
echo ""
echo -e "  ${YELLOW}⚠  Solo para uso legal y educativo.${NC}"
echo ""
