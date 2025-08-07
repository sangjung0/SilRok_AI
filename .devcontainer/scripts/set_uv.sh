#!/usr/bin/env bash
set -e

WORK_DIR="/workspaces/dev/"
cd "${WORK_DIR}"

uv sync --group dev
