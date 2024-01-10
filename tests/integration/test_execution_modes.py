import re
from pathlib import Path

from pytest_virtualenv import VirtualEnv


def test_taskfiles_works_with_tasks_in_home(
    git_repo_pth, ctx, run, virtualenv: VirtualEnv
):
    """
    This test tries to assert that task
    """
    virtualenv.run("pip install invoke")
    workspace = Path(virtualenv.workspace)

    user_folder = workspace / "home" / "user"
    tasks_folder = user_folder / "tasks"
    some_project_foder = user_folder / "project"

    user_folder.mkdir(parents=True)
    tasks_folder.mkdir(parents=True)
    some_project_foder.mkdir(parents=True)

    archive = workspace / "tasks.zip"

    run(f"git -C {git_repo_pth} archive -o {archive} HEAD")
    with ctx.cd(tasks_folder):
        run(f"unzip {archive}")
    with ctx.cd(some_project_foder):
        listing_of_tasks = run("inv -l").stdout
    tasks = re.findall(r"^  (?P<name>\w[\w-]+)\s+", listing_of_tasks, re.MULTILINE)
    assert len(tasks), "No tasks found in "
