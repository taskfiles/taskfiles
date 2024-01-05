"""
Retrieve binaries from release websites (github particularly fist supported).

"""

from typing import Dict

from invoke import Context, task


class Downloadable:
    ...


class GithubProject(Downloadable):
    project: str  # = 'junegunn/fzf/'
    # Defines
    binary: str  # = 'fzf'
    # 'fzf-0.44.1-linux_ppc64le.tar.gz'
    archive_format: str = ""  # 'fzf-{version}-{os}-{platform}'
    substitutions: Dict[str, str] = FileNotFoundError()


@task()
def populate_download_specs(ctx: Context):
    ctx.setup.download_specs = {}


@task(
    pre=populate_download_specs,
)
def download_binary(ctx: Context, name: str, version="latest"):
    ...
