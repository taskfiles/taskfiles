import re
from pathlib import Path

import pytest
from pytest_virtualenv import VirtualEnv

TASK_RE = r"^  (?P<name>\w[\w-]+)\s+"


@pytest.mark.external
def test_taskfiles_works_with_tasks_in_home(
    ctx,
    run,
    virtualenv: VirtualEnv,
    tasks_folder_in_workspace,
    workspace,
):
    """
    This test tries to assert that task
    """
    virtualenv.run("pip install invoke")
    root = workspace.workspace

    user_folder = root / "home" / "user"
    some_project_folder = user_folder / "project"

    user_folder.mkdir(parents=True)
    some_project_folder.mkdir(parents=True)

    with ctx.cd(some_project_folder):
        listing_of_tasks = run("inv -l").stdout
    tasks = re.findall(TASK_RE, listing_of_tasks, re.MULTILINE)
    assert len(tasks), f"No tasks found in {tasks_folder_in_workspace}"


def test_taskfiles_runs_as_a_program(
    installable_package_dir: Path,
    virtualenv: VirtualEnv,
    ctx,
    run,
):
    """
    Tests a Python package run as python -m taskfiles (which triggers __main__
    and program)
    """
    virtualenv.run(f"pip install --find-links {installable_package_dir} taskfiles")
    out = run(f"{virtualenv.python} -m taskfiles").stdout
    tasks = re.findall(TASK_RE, out, re.MULTILINE)
    assert len(tasks), "No task where found"


def test_taskfiles_lists_tasks(task_binary: Path, run):
    """
    Test that taskfiles run as a binary (with pyoxidizer)
    """
    out = run(
        task_binary,
    ).stdout
    tasks = re.findall(TASK_RE, out, re.MULTILINE)

    assert len(tasks), "No task where found"


def test_binary_local_tasks(workspace_with_binary, workspace_run):
    """
    Test that taskfiles run as a binary (with pyoxidizer)
    """
    out = workspace_run(
        "tsk",
    ).stdout
    tasks = re.findall(TASK_RE, out, re.MULTILINE)
    assert len(tasks), "No task where found"
