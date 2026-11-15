#!/usr/bin/env bash
set -euo pipefail

SIM_DIR="/root/mrc-sim/htsim/htsim/sim"
JOBS="$(nproc 2>/dev/null || echo 4)"

echo "[MRC-SIM] Building htsim_uec, htsim_eqds, and parse_output using ${JOBS} jobs..."
cd "${SIM_DIR}"
make -f Makefile.mrc -j"${JOBS}" all

echo "[MRC-SIM] Build complete:"
ls -lh "${SIM_DIR}/datacenter/htsim_uec" "${SIM_DIR}/datacenter/htsim_eqds" "${SIM_DIR}/parse_output"
