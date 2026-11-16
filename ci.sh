#!/usr/bin/env bash
# CI: ERC, DRC, Gerber files and the full agent check on the committed design.
# Routing is not repeated here: the routed board is part of the repository.
set -euo pipefail
cd "$(dirname "$0")"

echo "ci: KiCad $(kicad-cli version), $(python3 --version)"
python3 tools/fab.py --no-render
python3 .github/agent-tools/check.py

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo "### PCB checks passed (KiCad $(kicad-cli version))"
    echo "- ERC: 0 violations, DRC: 0 violations / 0 unconnected / 0 parity issues"
    echo "- Gerber files: $(ls output/gerbers | wc -l) in \`lab2-fab\` artifact"
  } >> "${GITHUB_STEP_SUMMARY}"
fi
echo "ci: OK"
