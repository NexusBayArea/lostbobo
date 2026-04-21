#!/bin/bash
set -euo pipefail
ruff check . --fix
ruff check .
