#!/usr/bin/env bash
# Устанавливает инструменты разработки для Ubuntu 24.04 в WSL.

set -Eeuo pipefail

target_user="${1:-${SUDO_USER:-}}"

require_root() {
  # Проверяет права для установки системных пакетов.
  if [[ "$EUID" -ne 0 || -z "$target_user" ]]; then
    printf 'Запустите сценарий от root и передайте имя WSL-пользователя.\n' >&2
    exit 2
  fi
}

configure_docker_repository() {
  # Добавляет официальный репозиторий Docker Engine.
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  printf '%s\n' 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable' > /etc/apt/sources.list.d/docker.list
}

configure_node_repository() {
  # Добавляет репозиторий Node.js 24.
  curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
}

install_uv_and_python() {
  # Устанавливает uv и Python 3.13 для WSL-пользователя.
  local user_home
  user_home="$(getent passwd "$target_user" | cut -d: -f6)"
  runuser -u "$target_user" -- env HOME="$user_home" bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
  touch "$user_home/.profile"
  if ! grep --fixed-strings --quiet 'export PATH="$HOME/.local/bin:$PATH"' "$user_home/.profile"; then
    printf '%s\n' 'export PATH="$HOME/.local/bin:$PATH"' >> "$user_home/.profile"
    chown "$target_user:$target_user" "$user_home/.profile"
  fi
  runuser -u "$target_user" -- env HOME="$user_home" "$user_home/.local/bin/uv" python install 3.13
}

require_root
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ca-certificates \
  curl \
  git \
  make \
  libasound2t64 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libatspi2.0-0 \
  libcairo2 \
  libcups2t64 \
  libdbus-1-3 \
  libdrm2 \
  libgbm1 \
  libglib2.0-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libwayland-client0 \
  libx11-6 \
  libxcb1 \
  libxcomposite1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxkbcommon0 \
  libxrandr2
configure_docker_repository
configure_node_repository
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin nodejs
usermod -aG docker "$target_user"
systemctl enable --now docker
install_uv_and_python
