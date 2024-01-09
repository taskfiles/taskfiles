import re
from pathlib import Path

import pytest
from pytest_virtualenv import VirtualEnv

VERSION_RE = r"^\d(\.\d)+$"


@pytest.mark.package
def test_package_installation(
    virtualenv: VirtualEnv, dist_wheel_path: Path, tmp_path: Path
):
    virtualenv.run(f"pip install --find-links {dist_wheel_path} taskfiles")
    out = tmp_path / "out.txt"
    virtualenv.run(f"pip list | grep taskfiles > {out}")
    result = out.read_text().strip()
    assert result, "No package installed by pip"
    _, version, *_ = re.split(r"\s+", result)
    assert (
        re.match(VERSION_RE, version) is not None
    ), f"Version {version} doesn't match with {VERSION_RE}"
    virtualenv.run("python -c 'import taskfiles;'")
