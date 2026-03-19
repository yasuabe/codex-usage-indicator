#!/usr/bin/env bash
set -euo pipefail

APP_NAME="codex-usage-indicator"
DISPLAY_NAME="Codex Usage Indicator"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_DIR="${INSTALL_DIR}/bin"
INSTALLED_BIN="${BIN_DIR}/${APP_NAME}"
LAUNCHER_DIR="${HOME}/.local/bin"
LAUNCHER_PATH="${LAUNCHER_DIR}/${APP_NAME}"
AUTOSTART_DIR="${HOME}/.config/autostart"
DESKTOP_PATH="${AUTOSTART_DIR}/${APP_NAME}.desktop"

DRY_RUN=false
NO_AUTOSTART=false
START_NOW=false

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --dry-run       Print actions without changing files.
  --no-autostart  Do not create ~/.config/autostart/*.desktop.
  --start-now     Launch indicator immediately after install.
  -h, --help      Show this help.
EOF
}

log() {
  printf '[install] %s\n' "$*"
}

run() {
  if "${DRY_RUN}"; then
    printf '[dry-run] %q' "$1"
    shift || true
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
  else
    "$@"
  fi
}

write_file() {
  local path="$1"
  local content="$2"
  if "${DRY_RUN}"; then
    printf '[dry-run] write %s\n' "${path}"
  else
    printf '%s' "${content}" > "${path}"
  fi
}

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --no-autostart) NO_AUTOSTART=true ;;
    --start-now) START_NOW=true ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ ! -f "${SCRIPT_DIR}/Cargo.toml" || ! -f "${SCRIPT_DIR}/src/bin/indicator.rs" ]]; then
  printf 'Error: run this script from project root.\n' >&2
  exit 1
fi

if ! command -v cargo >/dev/null 2>&1; then
  printf 'Error: cargo is required.\n' >&2
  exit 1
fi

log "Building release binary"
run cargo build --release --bin indicator --manifest-path "${SCRIPT_DIR}/Cargo.toml"

if [[ ! -f "${SCRIPT_DIR}/target/release/indicator" && "${DRY_RUN}" = false ]]; then
  printf 'Error: built binary not found: %s\n' "${SCRIPT_DIR}/target/release/indicator" >&2
  exit 1
fi

log "Installing into ${INSTALL_DIR}"
run mkdir -p "${BIN_DIR}" "${LAUNCHER_DIR}"
run cp -f "${SCRIPT_DIR}/target/release/indicator" "${INSTALLED_BIN}"
run chmod +x "${INSTALLED_BIN}"

launcher_content="$(cat <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${INSTALLED_BIN}" "\$@"
EOF
)"
write_file "${LAUNCHER_PATH}" "${launcher_content}"
run chmod +x "${LAUNCHER_PATH}"

if ! "${NO_AUTOSTART}"; then
  run mkdir -p "${AUTOSTART_DIR}"
  desktop_content="$(cat <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=${DISPLAY_NAME}
Comment=Show Codex usage in the top bar
Exec=${LAUNCHER_PATH}
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF
)"
  write_file "${DESKTOP_PATH}" "${desktop_content}"
  log "Created autostart entry: ${DESKTOP_PATH}"
fi

if "${START_NOW}"; then
  if "${DRY_RUN}"; then
    printf '[dry-run] start %q\n' "${LAUNCHER_PATH}"
  else
    nohup "${LAUNCHER_PATH}" >/dev/null 2>&1 &
  fi
fi

cat <<EOF
Done.
- install dir: ${INSTALL_DIR}
- launcher:    ${LAUNCHER_PATH}
- autostart:   $(if "${NO_AUTOSTART}"; then echo "skipped"; else echo "${DESKTOP_PATH}"; fi)

System packages required (Ubuntu):
  sudo apt install cargo pkg-config libgtk-3-dev libayatana-appindicator3-dev
EOF
