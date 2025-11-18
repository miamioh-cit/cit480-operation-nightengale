#!/usr/bin/env bash
set -e

SPLUNK_TGZ_URL="${SPLUNK_TGZ_URL:-https://download.splunk.com/products/splunk/releases/9.2.0/linux/splunk-9.2.0-a1234567890-Linux-x86_64.tgz}"
SPLUNK_INSTALL_DIR="/opt/splunk"
SPLUNK_USER="splunk"

echo "[*] Updating packages..."
sudo apt-get update -y

echo "[*] Creating splunk user (if not exists)..."
if ! id -u "${SPLUNK_USER}" >/dev/null 2>&1; then
  sudo useradd -m -s /bin/bash "${SPLUNK_USER}"
fi

echo "[*] Downloading Splunk package..."
sudo mkdir -p /tmp/splunk
sudo rm -f /tmp/splunk/splunk.tgz
sudo wget -O /tmp/splunk/splunk.tgz "${SPLUNK_TGZ_URL}"

echo "[*] Extracting Splunk to ${SPLUNK_INSTALL_DIR}..."
sudo mkdir -p /opt
sudo tar -xzf /tmp/splunk/splunk.tgz -C /opt

if [ ! -d "${SPLUNK_INSTALL_DIR}" ]; then
  TARGET="$(ls -d /opt/splunk* | head -n 1)"
  sudo mv "$TARGET" "${SPLUNK_INSTALL_DIR}"
fi

echo "[*] Setting ownership..."
sudo chown -R ${SPLUNK_USER}:${SPLUNK_USER} "${SPLUNK_INSTALL_DIR}"

echo "[*] Starting Splunk (non-interactive)..."
sudo -u ${SPLUNK_USER} ${SPLUNK_INSTALL_DIR}/bin/splunk start   --accept-license   --answer-yes   --no-prompt

echo "[*] Enabling Splunk boot-start..."
sudo ${SPLUNK_INSTALL_DIR}/bin/splunk enable boot-start   -user ${SPLUNK_USER}   --accept-license   --answer-yes   --no-prompt

echo "[*] Splunk status:"
sudo ${SPLUNK_INSTALL_DIR}/bin/splunk status || true

echo "[*] Done."
