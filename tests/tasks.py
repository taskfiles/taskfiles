"""
This task file is for interactive testing only.
Use it as inv -r tests <command>
"""
from invoke import Context, task


@task()
def run_in_docker(
    ctx: Context,
    image="python:3-alpine",
    architecture=None,
    command="python3 -m pip install invoke; sh",
    mounts=["{toplevel}:/tasks"],
):
    toplevel = ctx.run("git rev-parse --show-toplevel", hide=True).stdout.strip()

    mounts = [f"-v {mount.format(toplevel=toplevel)}" for mount in mounts]
    volumes = " ".join(mounts)

    ctx.run(
        f"docker run --rm -ti {volumes} {image} sh -c '{command}'",
        pty=True,
    )


@task()
def run_docker_setup(
    ctx: Context,
    image="python:3-alpine",
    architecture=None,
    command="sh /tasks/setup.sh; bash",
):
    """Runs in docker and calls the setup script"""
    run_in_docker(ctx, image=image, architecture=architecture, command=command)


@task()
def run_docker_plain(
    ctx: Context,
    image="python:3-alpine",
    architecture=None,
    command="sh",
):
    """Runs in docker and calls the setup script"""
    run_in_docker(ctx, image=image, architecture=architecture, command=command)
