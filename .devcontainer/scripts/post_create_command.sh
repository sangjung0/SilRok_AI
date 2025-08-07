#!/usr/bin/env bash
set -euo pipefail

# 인자 확인
if [[ $# -lt 1 || -z "$1" ]]; then
    echo "Usage: $0 <username>" >&2
    exit 1
fi

USER="$1"

# 해당 유저가 실제로 존재하는지 확인
if ! id "$USER" &>/dev/null; then
    echo "Error: user '$USER' does not exist." >&2
    exit 1
fi

# 퍼미션 변경
sudo chown -R "$USER":"$USER" /workspaces/dev
sudo chown -R "$USER":"$USER" "/home/$USER/.cache"

bash /workspaces/dev/.devcontainer/scripts/set_uv.sh
