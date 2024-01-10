"""
This module is """
import subprocess
from datetime import datetime
from pathlib import Path
from shlex import split
from shutil import which
from typing import Any, Callable

import pytest
from invoke import Context
from invoke.runners import Result


@pytest.fixture(scope="session")
def docker():
    """"""
    path = which("docker")
    if not path:
        raise pytest.skip()
    return path


@pytest.fixture(scope="session")
def git_repo_pth() -> Path:
    """Gets the top level"""
    return Path(
        subprocess.check_output(split("git rev-parse --show-toplevel")).decode().strip()
    )


@pytest.fixture(
    scope="session",
)
def dist_wheel_path(git_repo_pth) -> Path:
    """
    Returns the place to tell pip where to find the package
    """
    subprocess.run(
        split("hatch build -ct"),
        cwd=git_repo_pth,
    )
    return git_repo_pth / "dist"


tags = []


@pytest.fixture(scope="session")
def build_image(docker, git_repo) -> Callable[[str, str], str]:
    """Build a docker image"""

    def builder(context=None, tag=None):
        global tags  # noqa: PLW0602
        time_tag = int(datetime.now().timestamp())
        if not tag:
            tag = f"inv:test-{time_tag}"
        context = context or git_repo
        command = split(f"{docker} build -t {tag} {context}")
        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError:
            raise
        tags.append(tag)
        return tag

    yield builder
    for tag in tags:
        try:
            subprocess.check_call(split(f"{docker} image rm {tag} "))
        except subprocess.CalledProcessError:
            print(f"Error deleting {tag}")


@pytest.fixture(scope="session")
def image(build_image) -> str:
    return build_image()


@pytest.fixture()
def ctx() -> Context:
    # TODO: Implement this
    return Context()


@pytest.fixture()
def run(ctx) -> Callable[[Any], Result]:
    def _run(*args, **kwargs) -> Result:
        # https://github.com/pyinvoke/invoke/issues/710#issuecomment-624534674
        kwargs.update(pty=True, in_stream=False)
        return ctx.run(*args, **kwargs)

    return _run


# @pytest.fixture()
# def collections(git_repo_pth) -> Collection:
#     """Gives the collection of tasks"""
#     cwd_save = os.getcwd()


#     ns = taskfiles.get_root_ns()
#     os.chdir(cwd_save)
#     return ns
