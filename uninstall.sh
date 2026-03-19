#!/usr/bin/env bash
set -euo pipefail

APP_NAME="codex-usage-indicator"
INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
LAUNCHER_PATH="${HOME}/.local/bin/${APP_NAME}"
DESKTOP_PATH="${HOME}/.config/autostart/${APP_NAME}.desktop"
PROCESS_PATTERN="${INSTALL_DIR}/bin/${APP_NAME}"

DRY_RUN=false
NO_STOP=false

usage() {
  cat <<'EOF'
Usage: ./uninstall.sh [options]

Options:
  --dry-run  Print actions without changing files.
  --no-stop  Do not try to stop running indicator process.
  -h, --help Show this help.
EOF
}

log() {
  printf '[uninstall] %s\n' "$*"
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

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --no-stop) NO_STOP=true ;;
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

if ! "${NO_STOP}"; then
  if "${DRY_RUN}"; then
    printf '[dry-run] pkill -f %q\n' "${PROCESS_PATTERN}"
  else
    pkill -f "${PROCESS_PATTERN}" >/dev/null 2>&1 || true
  fi
fi

if [[ -f "${DESKTOP_PATH}" ]]; then
  run rm -f "${DESKTOP_PATH}"
  log "$(if "${DRY_RUN}"; then echo "Would remove"; else echo "Removed"; fi) autostart entry"
fi

if [[ -f "${LAUNCHER_PATH}" ]]; then
  run rm -f "${LAUNCHER_PATH}"
  log "$(if "${DRY_RUN}"; then echo "Would remove"; else echo "Removed"; fi) launcher"
fi

if [[ -d "${INSTALL_DIR}" ]]; then
  run rm -rf "${INSTALL_DIR}"
  log "$(if "${DRY_RUN}"; then echo "Would remove"; else echo "Removed"; fi) install dir"
fi

cat <<EOF
Done.
- install:   $(if "${DRY_RUN}"; then echo "would remove ${INSTALL_DIR}"; else echo "removed/kept depending on existence (${INSTALL_DIR})"; fi)
- launcher:  $(if "${DRY_RUN}"; then echo "would remove ${LAUNCHER_PATH}"; else echo "removed/kept depending on existence (${LAUNCHER_PATH})"; fi)
- autostart: $(if "${DRY_RUN}"; then echo "would remove ${DESKTOP_PATH}"; else echo "removed/kept depending on existence (${DESKTOP_PATH})"; fi)
EOF
