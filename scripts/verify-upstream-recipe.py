#!/usr/bin/env python3
"""Verify Linkerd's web image benchmark plan."""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)

def main() -> int:
    try:
        command = tomllib.loads((ROOT / ".boringcache.toml").read_text())["adapters"]["docker"]["command"]
        require(command == ["docker", "buildx", "build", "--file", "upstream/web/Dockerfile", "--build-arg", "LINKERD_VERSION=__SOURCE_TAG__", "--tag", "linkerd2-web-benchmark:local", "upstream"], "Docker plan changed")
        activation = (ROOT / "scripts/activate-docker-plan.py").read_text()
        require('"--push"' in activation and "__SOURCE_TAG__" in activation, "Docker plan activation changed")
        wrapper = (ROOT / "upstream/bin/docker-build-web").read_text()
        require("docker_build web" in wrapper and "web/Dockerfile" in wrapper and "LINKERD_VERSION" in wrapper, "upstream web wrapper changed")
        build = (ROOT / "upstream/bin/_docker.sh").read_text()
        for fragment in ("SUPPORTED_ARCHS=${SUPPORTED_ARCHS:-linux/amd64,linux/arm64}", "docker buildx build", "--push"):
            require(fragment in build, f"upstream docker-build changed: {fragment}")
        release = (ROOT / "upstream/.github/workflows/release.yml").read_text()
        require("docker-target: multi-arch" in release and "docker-push: 1" in release and "component: ${{ matrix.component }}" in release, "upstream release projection changed")
        action = (ROOT / ".github/actions/linkerd2-docker-benchmark/action.yml").read_text()
        require(action.count("LINKERD_VERSION=${{ steps.scope.outputs.source_tag }}") == 1, "Actions/cache version arg drifted")
        require("platforms:" not in action, "benchmark must use the runner's native platform")
        require(action.count("Activate the BoringCache Docker plan") == 1, "BoringCache publication projection changed")
    except (KeyError, OSError, RuntimeError, tomllib.TOMLDecodeError) as error:
        print(f"Linkerd recipe mismatch: {error}", file=sys.stderr)
        return 1
    print("Verified Linkerd web image plan against bin/docker-build-web on the runner's native platform.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
