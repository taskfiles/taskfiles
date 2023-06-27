"""
Test that taskfiles run as a program
"""
import re
from itertools import pairwise
from pathlib import Path
from shlex import split
from subprocess import check_output, getstatusoutput
from typing import Annotated, Mapping

import pytest


@pytest.fixture(scope="session")
def git_root() -> Path:
    """Returns the repository top level"""
    output = check_output(split("git rev-parse --show-toplevel")).strip().decode()
    return Path(output)


PackageFormat = Annotated[str, "The package format, i.e.: .tar.gz, .whl, etc."]


def pkg_fmt_cleaner(input_) -> PackageFormat:
    return re.sub(r"[\[\]]", "", input_)


@pytest.fixture
def packages(git_root) -> Mapping[PackageFormat, Path]:
    command = f"bash -lc 'cd {git_root} && hatch build'"
    status, output = getstatusoutput(
        command,
    )
    if not status == 0:
        msg = "Can't build the whl package"
        raise ValueError(msg)
    format_and_file = [line for line in output.splitlines() if line]
    result = {
        pkg_fmt_cleaner(format_): git_root / file_
        for format_, file_ in pairwise(format_and_file)
    }
    return result


@pytest.mark.skip(reason="Program not implemented yet")
def test_program(packages: Mapping[PackageFormat, Path], virtualenv, subtests, capsys):
    for i, (format_, path) in enumerate(packages.items()):
        with subtests.test(msg=format_, i=i):
            virtualenv.run(f"pip install {path}")
