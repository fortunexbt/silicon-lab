# Local decode speed of Cyber-Tiel-Coder-35B-A3B on a 24 GB M4

## Headline

**42.13 tok/s** median decode (greedy, MTP depth 2 plus n-gram drafting) over five prompts, one clean run on 2026-10-19 on an Apple M4 MacBook (24 GB, AC power, load 2.23). Per-prompt range 24.18 to 46.21 tok/s; mean 38.09; median time to first token 0.34 s.

This is not an A-B-B-A experiment and has no confidence interval. The spread above is across prompts, which differ in how predictable their text is, not across repeated paired blocks. The repeat analysis below is the only estimate of run-to-run noise.

| Prompt | Decode (tok/s) | TTFT (s) | Tokens |
|---|---:|---:|---:|
| code | 43.97 | 0.32 | 384 |
| math | 42.13 | 0.35 | 355 |
| prose | 24.18 | 0.34 | 384 |
| explain | 33.95 | 0.33 | 384 |
| codecont | 46.21 | 0.66 | 384 |

Task evals on the same server: tool-call accuracy 1.0, HumanEval 40-problem pass@1 0.95 (elapsed 173 s). Forty problems is a small sample: one problem is 2.5 points.

## Run-to-run noise

The same configuration (`d2_ub512`, depth 2 with -ub 512) was measured several times across the sweep, which gives a rough noise estimate. The first run is cold.

| Tag | Short decode (tok/s) |
|---|---:|
| q3 | 37.87 |
| q3 | 42.18 |
| q3r2 | 42.89 |
| q3r2idle | 42.77 |
| q3master | 42.98 |

Cold first run 37.87; the 4 later runs span 42.18 to 42.98 tok/s (mean 42.70, sample SD 0.36). Treat differences under about 0.8 tok/s between configurations as noise. The last row used a newer llama.cpp build, so it also mixes in a build difference.

## Full sweep

All 37 rows of `pareto.jsonl`, one measurement each, sorted by short decode. Every row is flagged clean (AC power, load at most 6.0). Prefill and long-decode figures are tok/s; accept is the draft acceptance rate.

| Tag | Config | Short decode | 32k decode | Prefill 10k | Prefill 32k | Accept | Load |
|---|---|---:|---:|---:|---:|---:|---:|
| q3r2 | ngram_dflash | 45.74 | 30.38 | 363.1 | 284.6 | 0.503 | 2.03 |
| q3r2 | dflash | 45.62 | 28.45 | 360.3 | 285.9 | 0.506 | 1.32 |
| q3r2 | d2_pmin03 | 43.04 | 28.81 | 352.5 | 274.7 | 0.683 | 2.4 |
| q3r2 | ngram_mtp2 | 43.03 | 29.83 | 350.7 | 274.6 | 0.624 | 2.28 |
| q3r2 | d2_ctxcp8 | 43.01 | 28.86 | 351.9 | 274.7 | 0.641 | 1.51 |
| q3master | d2_ub512 | 42.98 | 28.97 | 346.4 | 273.2 | 0.641 | 5.45 |
| q3r2idle | d2_keepalive | 42.92 | 28.96 | 365.1 | 276.2 | 0.641 | 1.83 |
| q3r2 | d2_ub512 | 42.89 | 28.84 | 348.5 | 274.4 | 0.641 | 1.24 |
| q3r2 | combo_d2 | 42.89 | 28.04 | 386.8 | 292.9 | 0.623 | 1.16 |
| q3r2idle | d2_ub512 | 42.77 | 28.57 | 353.1 | 274.8 | 0.641 | 2.58 |
| q3r2 | d2_ctxcp8_cram2048 | 42.73 | 29.61 | 351.9 | 274.6 | 0.642 | 3.98 |
| q3 | d2_ub2048 | 42.24 | 28.83 | 387.1 | 292.6 | 0.623 | 1.82 |
| q3 | d2_mlock | 42.22 | 29.03 | 347.4 | 273.9 | 0.641 | 2.52 |
| q3 | d2_cram2048 | 42.18 | 28.99 | 351.0 | 274.7 | 0.641 | 1.19 |
| q3 | d2_ub512 | 42.18 | 29.02 | 351.5 | 274.7 | 0.641 | 1.75 |
| q3 | d2_ub4096 | 42.06 | 28.68 | 353.7 | 271.9 | 0.623 | 1.79 |
| q3 | d2_cram0 | 41.9 | 29.51 | 354.6 | 274.8 | 0.642 | 3.2 |
| q3 | d2_ub1024 | 41.89 | 29.52 | 387.9 | 288.8 | 0.628 | 5.01 |
| q3r2 | k4v_mtp2 | 41.79 | 28.9 | 351.6 | 275.2 | 0.64 | 3.64 |
| q3 | d3 | 40.51 | 28.57 | 352.3 | 274.5 | 0.516 | 1.75 |
| q3r2 | combo_ngram_d1 | 39.99 | 29.52 | 387.0 | 293.9 | 0.726 | 1.57 |
| q3pr30139 | d2_ub512 | 39.98 | 27.53 | 350.9 | 270.7 | 0.641 | 3.25 |
| q3r2 | d1 | 39.91 | 31.05 | 350.3 | 274.9 | 0.77 | 1.25 |
| iq4 | d2_ub512 | 39.88 | 30.34 | 343.2 | 273.6 | 0.607 | 1.5 |
| q3r2 | combo_d1 | 39.85 | 30.71 | 387.8 | 293.3 | 0.764 | 1.35 |
| q3 | d3_pmin06 | 39.52 | 28.65 | 348.3 | 269.8 | 0.808 | 1.57 |
| iq4 | d2_ub2048 | 39.5 | 30.62 | 385.3 | 292.9 | 0.632 | 1.48 |
| q3 | d1 | 39.25 | 31.52 | 350.8 | 274.7 | 0.77 | 1.49 |
| iq4 | d2_mlock | 38.82 | 29.95 | 346.7 | 272.1 | 0.607 | 2.59 |
| q3 | d2_kvq8 | 38.14 | 25.32 | 341.7 | 269.1 | 0.641 | 1.58 |
| q3 | d2_ub512 | 37.87 | 26.59 | 352.8 | 258.5 | 0.641 | 4.8 |
| q3 | d4_pmin06 | 37.76 | 27.46 | 348.9 | 270.7 | 0.789 | 1.79 |
| ice19 | d2_ub512 | 37.16 | 27.02 | 346.0 | 274.4 | 0.64 | 1.45 |
| ice19 | ngram_mtp2 | 37.06 | 26.77 | 355.5 | 274.6 | 0.602 | 1.98 |
| ice19 | d1 | 36.7 | 28.99 | 352.9 | 273.2 | 0.769 | 5.32 |
| iq4 | d3 | 36.13 | 29.29 | 344.1 | 270.0 | 0.506 | 2.51 |
| q3r2 | dflash_n8 | 33.67 | 16.72 | 356.0 | 282.7 | 0.239 | 1.76 |

Several `dflash` rows decode faster on the short prompt (about 45.6 tok/s) than the depth-2 default, with 32k decode no better. Those are single measurements within a few tok/s of the noise band above, and this report does not claim they are faster or slower.

## Limits

- One machine, one clean headline run. No paired blocks, no interval. The spread is across
  prompts.
- The sweep rows are single measurements, with the A-B-B-A drift control absent. Row order in
  the file is the order they ran, and configs were not interleaved, so thermal or memory
  drift is confounded with config.
- The headline run used the Homebrew `llama-server` 0.7.0 binary; its exact build number was
  not recorded. Only the `q3master` row is tied to a recorded build (master build 11738,
  commit `f174553e1621c6a22a64e7bfcbb58d3a5c49e6fb`).
- The model licence for Cyber-Tiel-Coder-35B-A3B was not verified, so no weights or outputs
  are republished here, only throughput numbers.
- Decode speed under speculative drafting depends on how repetitive the text is. The
  `prose` prompt (24.18 tok/s) and `codecont` (46.21 tok/s) differ by nearly 2x on the same
  model and settings. Do not quote one number as general speed.
- Memory was tight: swap was 4.3 GB at the start of the headline run and the sweep rows
  record swap and pageout deltas. A fresh reboot resets `iogpu.wired_limit_mb`.

## Recipe

| Input | Value |
|---|---|
| Machine | Apple M4, 24 GB unified memory, AC power |
| Server | `data/serve_cyber_omp.sh` (copy of the original script), depth 2 |
| Model file | `Cyber-Tiel-Coder-35B-A3B-MTP-UD-Q3_K_XL.gguf`, served as `cyber-tiel-35b` |
| Server flags | `-ngl 99 -fa on -c 65536 -np 1 -ub 2048 --temp 0 --jinja` |
| Speculation | `--spec-type ngram-mod,draft-mtp --spec-draft-n-max 2`, ngram-mod n-match 24, n-min 48, n-max 64 |
| Wired limit | `sudo sysctl iogpu.wired_limit_mb=20480` (resets on reboot) |
| Benchmark | `bench_server.py --url http://127.0.0.1:8080/v1 --model cyber-tiel-35b --temp 0 --tag cyber_tiel_depth2` |
| Task evals | `eval_tasks.py` with the same url, model and tag |

`bench_server.py`, `eval_tasks.py` and `pareto_sweep.py` live in the source project and
are not part of this repository. `data/pareto.jsonl` is the unedited
sweep log and `data/queue_excerpt.log` is lines 47 to 58 of its `queue.log`. Rebuild this
report with `python reports/qwen38/build.py`. Reproducing the measurement needs the model
file, the scripts and an M4-class machine. This repository ran no model.
