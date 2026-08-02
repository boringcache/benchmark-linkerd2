# benchmark-linkerd2

Isolated Linkerd2 benchmark runner for BoringCache vs GitHub Actions cache.

Stable BoringCache workflows install the verified CLI `v1.16.4` release;
canary dispatches must use an exact immutable CLI tag.

The first fixture targets Linkerd's `web/Dockerfile`. A recent full pull-request
run [`30044625065`](https://github.com/linkerd/linkerd2/actions/runs/30044625065)
spent 208.6 seconds preparing
and sending that image's `type=gha,mode=max` cache. The same run built six
cache-exporting Docker jobs and spent about 8m07s of runner time across their
export tails.

The integration workflow recorded 168 runs in the 30 days ending 2026-07-24,
or about 5.6 runs per day. At inspection time the Actions cache API reported
10.64 GB across 194 active entries, already beyond GitHub's historical 10 GB
repository allowance.

This repo exists separately from the central benchmarks publisher so Linkerd2 can have:

- a pinned upstream source commit
- isolated GitHub Actions cache usage
- one per-repo BoringCache workspace name: `boringcache/benchmark-linkerd2-v2`
- independent benchmark runs triggered by upstream sync commits and manual dispatches

## Source Model

- upstream app source lives in the pinned `upstream/` submodule
- workflows build upstream `web/Dockerfile` with `upstream/` as the Docker context
- builds pass the same `LINKERD_VERSION` argument as Linkerd's
  `bin/docker-build-web` wrapper

Currently pinned upstream source:

- see the committed `upstream/` submodule on `main`; the measured proof series
  below remains fixed

## Rolling Proof Series

The benchmark replays these three linear `main` merge commits oldest to
newest. Each associated PR successfully ran the upstream `build-ext (web)`
Docker job:

| Merge commit | Upstream proof |
| --- | --- |
| `eb392d88c6ab5b3928c4ee86b18b7995a094fc9d` | [PR #15508 run 29975955853](https://github.com/linkerd/linkerd2/actions/runs/29975955853) |
| `20429bc0c6bf91e3344650444acf160586051c8d` | [PR #15486 run 29927205759](https://github.com/linkerd/linkerd2/actions/runs/29927205759) |
| `88414c62846b82ed75c6301d5374b5c75982b4ae` | [PR #15499 run 30044625065](https://github.com/linkerd/linkerd2/actions/runs/30044625065) |

## Measured Results

The oldest commit populated each isolated `-proof` rolling cache and is not a
comparative sample. The next two runs imported only that strategy's preceding
rolling cache before building the changed upstream commit.

| Upstream commit | Run | GitHub Actions cache | BoringCache | Time saved | GHA export | BoringCache export |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `20429bc` | [30092111131](https://github.com/boringcache/benchmark-linkerd2/actions/runs/30092111131) | 157s | 127s | 30s (19%) | 37.1s | 0.4s |
| `88414c6` | [30092324077](https://github.com/boringcache/benchmark-linkerd2/actions/runs/30092324077) | 241s | 174s | 67s (28%) | 90.2s | 3.5s |
| **Average** | | **199s** | **151s** | **49s (24%)** | **63.7s** | **2.0s** |

Fresh run
[`30090999227`](https://github.com/boringcache/benchmark-linkerd2/actions/runs/30090999227)
measured a 322-second GitHub Actions cache cold build versus 193 seconds with
BoringCache, followed by same-ref warm builds of four and three seconds. The
fresh lane is a parity check; it does not seed or count toward the rolling
series above.

## Scenarios

- `cold`
- `warm1`

Fresh lane runs a no-prior-cache cold build plus one warm rerun on the same pinned source tree. Rolling lane records the upstream commit build as-is after each upstream sync against the prior rolling cache and skips `warm1`.

The two-entry matrix compares GitHub Actions cache with BoringCache managed
BuildKit. It does not call BoringCache inside Dockerfile `RUN` steps. This
Docker benchmark is intentionally separate from the
`linkerd2-proxy` Rust/sccache comparison so each published row has one measured
cache surface.

## Output

Each workflow uploads machine-readable JSON and Markdown summaries. Those artifacts are intended to be ingested by the central `boringcache/benchmarks` publisher later.

## Token Model

This repo uses split BoringCache tokens as the standard CI shape:

- `BORINGCACHE_RESTORE_TOKEN` for read-only restore and proxy access
- `BORINGCACHE_SAVE_TOKEN` for trusted write paths
