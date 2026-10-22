# Shader frame production on a base M4: repeat noise and matched pairs

## Headline: repeat noise on one configuration

Three 60 s captures of the same MakeUp lean profile on the jungle route, 1920x1200 output, averaged **71.49 CPU FPS** (sample SD 0.71, range 70.67 to 71.93). The seeded 95% bootstrap interval of the mean over n=3 is [70.67, 71.93]; with three values it is only a rough guide. This is the only run-to-run noise estimate in the evidence, so the pair table below treats differences within 1.3 FPS as inside the noise.

| Capture | Average CPU FPS | p95 interval (ms) | p99 interval (ms) | Intervals over 33 ms |
|---|---:|---:|---:|---:|
| makeup-lean-full1920-jungle-02 | 70.67 | 16.01 | 16.71 | 0 |
| makeup-lean-full1920-jungle-03 | 71.86 | 15.66 | 16.17 | 0 |
| makeup-lean-full1920-jungle-04 | 71.93 | 15.87 | 16.47 | 0 |

## Matched pairs

Each row compares two separate captures: B minus A in CPU FPS. There is one capture per arm, so there is no interval and no drift control; the last column compares the difference to the 1.3 FPS repeat range above.

| Question | A | B | A FPS | B FPS | B - A | Change | Against noise |
|---|---|---|---:|---:|---:|---:|---|
| Faithful 32x texture pack vs vanilla textures, jungle, R12/S12 | `makeup-lean-r12s12-full1920-jungle-screen-02` | `makeup-faithful32-r12s12-full1920-jungle-01` | 79.73 | 81.04 | +1.31 | +1.6% | outside noise |
| ZGC vs G1 garbage collector, fresh flight | `makeup-lean-entity-g1-full1920-freshflight-01` | `makeup-lean-entity-zgc-full1920-freshflight-01` | 69.34 | 69.47 | +0.13 | +0.2% | inside noise |
| Second flight vs first flight, same build | `makeup-core-entity-full1920-freshflight-01` | `makeup-core-entity-full1920-warmflight-01` | 69.26 | 74.81 | +5.55 | +8.0% | outside noise |
| Second flight vs first flight, C2ME build | `makeup-core-entity-c2me-full1920-freshflight-01` | `makeup-core-entity-c2me-full1920-warmflight-01` | 69.14 | 74.77 | +5.63 | +8.2% | outside noise |
| Frame cap 90 vs 120, vsync off, jungle (neither cap binds) | `makeup-r12s12-full1920-cap90-vsyncoff-jungle-02` | `makeup-r12s12-full1920-cap120-vsyncoff-jungle-01` | 80.16 | 80.70 | +0.53 | +0.7% | inside noise |
| Vsync on vs off at a 60 FPS cap (cap-bound by construction) | `makeup-r12s12-full1920-cap60-vsyncon-jungle-01` | `makeup-r12s12-full1920-cap60-vsyncoff-jungle-01` | 59.98 | 59.99 | +0.01 | +0.0% | inside noise |

The flight rows are an order effect, not a build effect: both pairs show the second flight over the same route about 5.5 FPS faster than the first, in two different builds, so first-flight captures are biased low and the later flight is the fairer number. The 60 FPS vsync rows land on the cap, so they say nothing about rendering cost. The cap 90 and 120 rows sit at about 80 FPS, below both caps, so they show the cap setting alone did not change throughput.

## River screen, quoted from the ledger

The ledger also records a river screen for the texture-pack comparison. Its raw capture is not in the evidence index, so these two numbers are quoted: vanilla 97.07 against Faithful 32x 97.36 CPU FPS (+0.29). The ledger's own reading: "Small single-screen differences; not a causal or general performance claim."

## Limits

- Scope: These are measurements from one base M4 MacBook Pro and the listed software. They do not predict performance on another Mac. The campaign ran 2026-09-29 through 2026-10-03 on a Base Apple M4 MacBook Pro (10 CPU cores, 10 GPU cores, 24 GiB).
- Metric: CPU frame production at Minecraft.renderFrame(boolean) return; each interval includes the frame limiter. It is not gpu completion or presentation, input-to-display latency, displayed frame rate.
- 15 of the 15 captures used here are marked `unreviewed` in the evidence index: the FPS is kept as source evidence, but integrity and visual validity were not reviewed. Those marks come from the source project and are carried over unchanged.
- Three repeats give a rough noise band, not a reliable interval. A band measured on the jungle route may not describe other routes.
- The pairs are not A-B-B-A: one capture per arm, taken at different times, so drift and the order effect shown above are confounded with the compared setting.
- Shader quality was not held equal across profiles, so FPS here is not a ranking of shader packs.

## Recipe and sources

| Input | Value |
|---|---|
| Source project | `minecraft-apple-silicon-framework`, commit `d9b3204a9959cdb25e3c6da2bed66affd9bd3885`, MIT licence |
| Source files | `evidence/captures.jsonl`, `evidence/ledger.json` |
| Selection | the capture ids listed in `PAIRS` and `REPEATS` in `build.py` |
| Extract | `cd reports/shader && python extract.py <path to evidence>` |
| Rebuild | `python reports/shader/build.py` |

`data/captures.jsonl` holds the selected records unedited, one per line, and `data/ledger.json`
is a byte copy. Each record carries the `source_ref` and `source_sha256` of the original
summary file, which is not copied here. This repository ran no Minecraft or shader
benchmark; it recomputes differences and the interval from the committed records.
