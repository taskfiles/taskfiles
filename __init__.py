"""
This top level __init__ is not intended to make the root
directory a package but to support the use of the repo itself
as a task module. i.e.: git clone git@work.github.com:taskfiles/taskfiles.git ~/tasks
"""  # noqa: N999
import sys
from pathlib import Path

if "__file__" in globals():
    # We use absolute and not resolve here to prevent
    # issues with symlinking
    path = Path(__file__).absolute()
    directory = path.parent
    if directory.name == "tasks":
        sys.path.insert(0, str(directory / "src"))

        from taskfiles import get_root_ns

        ns = get_root_ns()
