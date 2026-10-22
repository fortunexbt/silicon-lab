#!/bin/zsh
# Serve Cyber-Tiel-Coder-35B-A3B for Oh-My-Pi (omp). Authorized security-testing
# use: this serves a model, it generates no attack content.
# --jinja: tool/function calling (omp is an agent).
# -c 65536: f16 KV fits swap-free on this 24GB M4 (verified: 62.2k-token prefill,
#          9 MiB pageouts, no swap growth). 32k left omp ~6K usable tokens after
#          its 10K prompt and compaction reserve.
# -np 1:   one agent, one slot. Avoids any draft-mtp multi-slot interaction and
#          the 3 idle slots llama-server would otherwise allocate.
# (No --cache-reuse: this build reports "cache_reuse is not supported by this
#  context" and disables it, since the hybrid-linear-attention KV can't be shifted.)
# --temp 0: greedy when the client omits temperature. omp's default (temperature:
#          -1 = provider default) omits it, so this keeps the sweep's greedy MTP
#          acceptance. omp also takes a top-level `temperature: 0` in
#          ~/.omp/agent/config.yml, but that applies to every omp model.
# -ub 2048: +10% prefill at 10K, +6.5% at 32K vs the default 512 (pareto_sweep.py).
# ngram-mod in front of MTP: n-gram drafts copy repeated text (file edits, diffs) at
#          ~120 tok/s vs ~48 for MTP alone, with no loss elsewhere; MTP covers the rest.
# Binary: llama.cpp master built by build_llama.sh (same speed as Homebrew 0.7.0, plus
#          the Metal MoE-reduce race fix #30795); falls back to Homebrew if absent.
# Depth 0 => serve plain (no speculation); depth>0 => n-gram + MTP self-speculation.
MODEL="${2:-/Users/fortune/.lmstudio/models/peculiar-ragdoll/Cyber-Tiel-Coder-35B-A3B-GGUF-MTP/Cyber-Tiel-Coder-35B-A3B-MTP-UD-Q3_K_XL.gguf}"
DEPTH="${1:-2}"
# iogpu.wired_limit_mb resets to 0 (macOS default, ~16 GiB) on reboot; 64k ctx with
# -ngl 99 projects 17,447 MiB of Metal memory before the MTP draft context, and
# the explicit -ngl stops llama.cpp's --fit from offloading, so warn early.
wired=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo 0)
(( wired >= 20480 )) || print -u2 "WARN: iogpu.wired_limit_mb is $wired (recommend: sudo sysctl iogpu.wired_limit_mb=20480 to avoid Metal OOM/paging at 64k ctx)"
spec=()
[[ "$DEPTH" -gt 0 ]] && spec=(--spec-type ngram-mod,draft-mtp --spec-draft-n-max "$DEPTH"
  --spec-ngram-mod-n-match 24 --spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64)
BIN="${0:A:h}/llama.cpp-master/build/bin/llama-server"
[[ -x "$BIN" ]] || BIN=llama-server
exec "$BIN" -m "$MODEL" --alias cyber-tiel-35b --host 127.0.0.1 --port 8080 \
  -ngl 99 -fa on -c 65536 -np 1 -ub 2048 --temp 0 --jinja "${spec[@]}"
