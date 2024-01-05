"""
Tasks to interact with CNCF's Lima (https://www.cncf.io/projects/lima/)
"""
import re
import sys
from pathlib import Path
from shutil import copy, which
from typing import Dict

from invoke import Context, task


def lima_ssh_output_to_dict(output: str) -> Dict[str, str]:
    options = re.findall(r"(?<=-o\s)[\w\d\'\"\=/\.\^\@\-\,]+", output)
    options = [string.strip("'") for string in options]
    options_dict = dict(map(lambda s: s.split("=", maxsplit=1), options))
    return options_dict


def create_config_file(path: Path, host: str, config_dict: Dict[str, str]) -> None:
    lines = [f"Host {host}"]
    lines.extend(f"\t{key} {value}" for key, value in config_dict.items())
    lines.append("")  # Final new line
    path.write_text("\n".join(lines))


@task()
def lima_ssh_to_config(ctx: Context, name=None, verbose=False):
    """Adds SSH config for a host controlled by lima.
    This will use ~/.ssh/config.d/name.config and use the Include directive in
    ~/.ssh/config
    """
    if not which("limactl"):
        sys.exit("Please install limactl first")
    if not name:
        sys.exit("No name provided")
    output = ctx.run(f"limactl show-ssh {name}", hide=not verbose).stdout.strip()
    host = output.split(" ")[-1]
    options_dict = lima_ssh_output_to_dict(output=output)
    config_dir = Path("~/.ssh/config.d").expanduser()
    config_dir.mkdir(exist_ok=True, parents=True)
    config_file = config_dir / f"{host}.config"
    create_config_file(path=config_file, host=host, config_dict=options_dict)
    print(f"Config {config_file} written.")
    ssh_config = Path("~/.ssh/config").expanduser()

    lines = ssh_config.read_text().splitlines()
    to_add = f"Include {config_file}"
    if to_add not in lines:
        if verbose:
            print(f"Line {to_add} not present in {ssh_config}, adding...")
        ssh_config_backup = Path("~/.ssh/config~").expanduser()
        if verbose:
            print(f"Backing up {ssh_config} as {ssh_config_backup}", file=sys.stderr)
        copy(ssh_config, ssh_config_backup)
        lines.extend(
            [
                f"# Config added for lima host {host}",
                to_add,
            ]
        )
        ssh_config.write_text("\n".join(lines))
        print(f"{ssh_config} updated.")
    else:
        print(f'Line "{to_add}" already present in {ssh_config}, run\nssh {host}')
