"""
This module is """
import base64
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from shlex import split
from shutil import which
from typing import Callable, Dict, List

import pytest
from invoke import Context
from invoke.runners import Result
from typing_extensions import Annotated


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
    if not which("git"):
        pytest.fail("git binary not available")

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


def path2str(run_args) -> str:
    if isinstance(run_args[0], Path):
        path_str = (str(run_args[0]),)
        remaining = run_args[1:]
        return path_str + remaining
    else:
        return run_args


@pytest.fixture()
def run(ctx) -> Callable[[str, Path], Result]:
    def _run(*args, **kwargs) -> Result:
        # https://github.com/pyinvoke/invoke/issues/710#issuecomment-624534674
        kwargs.update(pty=True, in_stream=False)
        args = path2str(args)
        return ctx.run(*args, **kwargs)

    return _run


@pytest.fixture()
def workspace_run(ctx, workspace) -> Callable[[str, Path], Result]:
    """Same as run, but adds the workspace.workspace Path to the PATH of run"""

    def _run(*args, **kwargs) -> Result:
        # https://github.com/pyinvoke/invoke/issues/710#issuecomment-624534674
        kwargs.update(pty=True, in_stream=False)
        args = path2str(args)
        env = kwargs.setdefault("env", {})
        path = env.setdefault("PATH", os.getenv("PATH"))
        env["PATH"] = f"{workspace.workspace}:{path}"
        return ctx.run(*args, **kwargs)

    return _run


@pytest.fixture()
def binary_name() -> str:
    return "tsk"


# @pytest.fixture()
# def collections(git_repo_pth) -> Collection:
#     """Gives the collection of tasks"""
#     cwd_save = os.getcwd()


#     ns = taskfiles.get_root_ns()
#     os.chdir(cwd_save)
#     return ns


@pytest.fixture()
def repo_zipfile(run, workspace, git_repo_pth) -> Path:
    archive = workspace.workspace / "tasks.zip"

    run(f"git -C {git_repo_pth} archive -o {archive} HEAD")
    return archive


@pytest.fixture()
def installable_package(
    tasks_folder_in_workspace,
    virtualenv,
) -> Path:
    virtualenv.run("pip install build")
    virtualenv.run(f"python -m build {tasks_folder_in_workspace} --wheel")
    dist = tasks_folder_in_workspace / "dist"
    wheels = dist.glob("*.whl")
    if len(wheels) > 1:
        pytest.fail(f"Multiple wheels found in {dist}")
    elif len(wheels) == 0:
        pytest.fail(f"No wheels produced in {dist}")

    return wheels[0]


@pytest.fixture()
def tasks_folder_in_workspace(workspace, repo_zipfile, ctx, run) -> Path:
    """A separate folder with the clean contests of the repo"""
    tasks: Path = workspace.workspace / "tasks"
    tasks.mkdir()
    with ctx.cd(tasks):
        run(f"unzip {repo_zipfile}")
    return tasks


@pytest.fixture()
def installable_package_dir(installable_package) -> Path:
    """Create a .whl file with the clean repo state"""
    return installable_package.parent


@dataclass
class BinaryCache:
    """Cache binaries for pytest.config.cache in JSON friendly way"""

    binary_b64: str = field(repr=False, default_factory=str)
    creation_time: datetime = field(
        default_factory=datetime.now,
    )

    def __post_init__(self):
        if isinstance(self.creation_time, str):
            self.creation_time = datetime.fromisoformat(self.creation_time)

    @classmethod
    def from_path(cls, path: Path) -> "BinaryCache":
        with path.open("rb") as fp:
            binary = fp.read()
            encoded = base64.b64encode(binary).decode("utf-8")
            return cls(
                binary_b64=encoded,
            )

    def write_to_path(self, path: Path) -> None:
        binary = base64.b64decode(self.binary_b64)
        with open(path, "wb") as fp:
            fp.write(binary)
        path.chmod(0o700)

    def to_json(self) -> Dict:
        return {
            "binary_b64": self.binary_b64,
            "creation_time": self.creation_time.isoformat(),
        }

    def content_length(self) -> int:
        return len(self.binary_b64)

    def is_valid(self) -> bool:
        # TODO: Check against src/taskfiles timestamps
        if self.content_length == 0 or not isinstance(self.binary_b64, str):
            return False
        return True


@pytest.fixture(
    # scope="module"
)
def task_binary(
    request,
    tasks_folder_in_workspace: Path,
    installable_package_dir,
    run,
    ctx,
    tmp_path,
    binary_name: str,
) -> Path:
    """
    Builds a binary with pyoxidizer and return the path to it
    """
    # This is a speedup but it's not thread safe yet
    bin_cache: BinaryCache = BinaryCache(
        request.config.cache.get("task_binary", default={})
    )
    if not bin_cache.is_valid():
        with ctx.cd(tasks_folder_in_workspace):
            res = run(
                "pyoxidizer build",
                env={
                    "PIP_FIND_LINKS": installable_package_dir,
                    "BUILD_PATH": tmp_path,
                },
            )
        out_err: List[str] = res.stdout.splitlines() + res.stderr.splitlines()
        line = [line for line in out_err if "installing files to" in line]
        *_, path = line[0].rsplit(" ")
        # XXX: Parametrize the name of the binary
        temp_binary = Path(path) / binary_name
        bin_cache = BinaryCache.from_path(temp_binary)
        request.config.cache.set("task_binary", bin_cache.to_json())
    target = tasks_folder_in_workspace / binary_name
    bin_cache.write_to_path(target)
    return target


WorkspaceWithBinary = Annotated[Path, "Directory with tsk binary"]


@pytest.fixture()
def workspace_with_binary(workspace, task_binary) -> WorkspaceWithBinary:
    shutil.copy(task_binary, workspace.workspace)
    return workspace_with_binary
