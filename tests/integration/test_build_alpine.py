import shlex
import subprocess

import pytest


@pytest.mark.skip(reason="Skipping docker image build")
def test_runs_in_alpine_linux_with_docker(docker, git_repo):
    options = f"--rm -v {git_repo}:/tasks"
    command = ";".join(
        [
            "apk add curl bash python3 gcompat",
            "python3 -m ensurepip",
            "python3 -m pip install invoke",
            "inv -l",
        ]
    )
    image = "alpine:3.17"
    cmd = f'{docker} run {options} {image} sh -c "{command}"'

    proc = subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    exit_code = proc.wait(timeout=3600)
    assert exit_code == 0, (
        f"Exit code of {proc} is {proc.stdout.read().decode()} "
        f"{proc.stderr.read().decode()}"
    )
