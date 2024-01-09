import inspect
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from shutil import which
from typing import Dict, List, Optional
from urllib.parse import urlparse

from invoke import Context, Task, task

# from .plugins import Plugin


@task()
def self_trace(
    ctx,
    query_: List[str] = [],
    verbose: bool = False,
    action: Optional[str] = "VarsSnooper",
):
    """
    Enables tracing of execution of the tasks.
    Consider this as bash -x with selections.

    For more sophisticated calls use PYTHONHUNTER=xxx inv yyy
    Read more about it at: https://python-hunter.readthedocs.io/en/latest/introduction.html#activation
    """
    try:
        import hunter
    except ImportError:
        sys.exit("hunter package not available")

    if not query_:
        query_ = ["module_sw=tasks"]

    def build_query(a_string):
        key, value = a_string.split(
            "=",
        )
        kw = {key: value}
        return hunter.Query(**kw)

    queries = [build_query(query) for query in query_]
    if verbose:
        print(queries, file=sys.stderr)

    hunter.trace(*queries, stdlib=False)


@task(
    autoprint=True,
)
def show_interpreter(ctx: Context):
    """Shows the Python interpreter being used"""
    return sys.executable


@task(autoprint=True)
def version(ctx: Context):
    """Shows the version of the taskfiles"""
    env_keys = ("COMMIT_ID", "GIT_BRANCH", "CHECKOUT_STATUS", "EXTRA_VERSION_INFO")
    info = {name: os.environ.get(name, "missing") for name in env_keys}
    return info


def _get_task_dict() -> Dict[str, Task]:
    # Old hacky implementation
    # execute_method = inspect.currentframe().f_back.f_back.f_back
    # collection = execute_method.f_locals["self"].collection
    # tasks_by_module: Dict[str, Any] = {}
    # for name, task_ in collection.tasks.items():
    #     task_for_mod = tasks_by_module.setdefault(task_.__module__, {})
    #     task_for_mod[name] = task_
    # return tasks_by_module
    from taskfiles import get_root_ns

    ns = get_root_ns()
    return ns.tasks


LINE_DEF_FORMAT = "({filename}, line {lineno})"


@dataclass
class TaskInfo:
    task: Task = field(repr=False)
    name: str = field(init=False)
    filename: Optional[str] = field(init=False, repr=False)
    lineno: Optional[int] = field(init=False, repr=False)
    source_lines: List[str] = field(init=False, repr=False)

    def __post_init__(self):
        self.name = self.task.name
        self.filename = getattr(sys.modules[self.task.body.__module__], "__file__", None)
        self.source_lines, self.lineno = inspect.getsourcelines(self.task.body)

    @classmethod
    def from_task(cls, task: Task) -> "TaskInfo":
        if not isinstance(task, Task):
            msg = f"{task}({type(task)}) is not an instance of Task"
            raise ValueError(msg)
        return cls(task=task)

    def __str__(self):
        return f"{self.filename}:{self.lineno}"


def get_task_location(task: Task) -> str:
    filename = getattr(sys.modules[task.body.__module__], "__file__", None)
    # filename = inspect.getfile(task_obj.body)
    source_lines, lineno = inspect.getsourcelines(task.body)

    return filename, lineno


# TODO: show getenv
@task(
    help={
        "indent_": "Indentation for entries (default to 2)",
        "show_line_def": "Shows the line definition",
        "line_def_format": "How to format the line, defaults to VSCode: "
        f"{LINE_DEF_FORMAT}",
        "show_internal": "Shows also the modules that are internal. "
        "These have a name that starts with underscore, e.g.: _utils",
    }
)
def list_tasks(
    ctx: Context,
    indent_: int = 2,
    show_line_def=True,
    line_def_format="({filename}, line {lineno})",
    show_internal=False,
) -> None:
    """
    Shows the tasks that have been loaded. This is a more detailed implementation
    than invoke -l.
    """
    from taskfiles import (
        TASKS_KEEP_MODULE_NAME_PREFIX,
        TASKS_LOAD_PLUGINS,
        TASKS_PLUGIN_DIRS,
    )

    # if TASKS_KEEP_MODULE_NAME_PREFIX:
    #     sys.exit("Not supported yet. Please TASKS_KEEP_MODULE_NAME_PREFIX=False")

    indent = f"{' ' * indent_}"
    # tasks = _get_task_dict()
    from taskfiles import get_root_ns

    ns = get_root_ns()

    to_iterate = {}
    if ns.collections:
        for name, collection in ns.collections.items():
            to_iterate[name] = collection
    to_iterate[""] = ns
    for coll_name, collection in sorted(to_iterate.items(), key=lambda tup: tup[0]):
        if not TASKS_KEEP_MODULE_NAME_PREFIX:
            ns_name = coll_name or "built-in"
        else:
            ns_name = coll_name or "core"
        print(ns_name)
        for task_name, task_ in collection.tasks.items():
            info = TaskInfo.from_task(task_)

            print(indent, task_name, info, sep=" ")

    # def is_a_task_module(name, module) -> bool:
    #     if name in sys.builtin_module_names:
    #         return False
    #     if name.startswith("tasks."):
    #         return True
    #     try:
    #         module_path = module.__file__ or ""
    #     except AttributeError:
    #         module_path = ""
    #     return "_plugins" in module_path

    # def get_sort_value(name):
    #     if "." in name:
    #         *_, name = name.split(".")
    #     return name

    # names: List[str,] = sorted(
    #     (name for name, module in sys.modules.items()
    #        if is_a_task_module(name, module)),
    #     key=get_sort_value,
    # )

    # for name in names:
    #     *_, sub_name = name.split(".", maxsplit=1)
    #     if "plugin" in sub_name:
    #         is_internal = False
    #     else:
    #         is_internal = sub_name.startswith("_")

    #     if is_internal and not show_internal:
    #         continue
    #     module = sys.modules[name]
    #     this_module_tasks = tasks.get(name)
    #     if not this_module_tasks:
    #         continue
    #     filename = getattr(module, "__file__", "not found")
    #     if sub_name.startswith("_plugins"):
    #         no_prefix = sub_name.replace("_plugins", "(plugin) ")
    #         pretty_name = no_prefix
    #     else:
    #         pretty_name = f".{sub_name}"
    #     msg = f"{pretty_name} (from file {filename})"
    #     print(msg)

    #     for task_name, task_obj in this_module_tasks.items():
    #         if show_line_def:
    #             filename = inspect.getfile(task_obj.body)
    #             source_lines, lineno = inspect.getsourcelines(task_obj.body)
    #             extra = line_def_format.format(**locals())
    #         else:
    #             extra = ""
    #         print(f"{indent}{task_name} {extra}")
    #     print("")

    print("Internal Configuration variables")
    print()
    print(f"TASKS_KEEP_MODULE_NAME_PREFIX={TASKS_KEEP_MODULE_NAME_PREFIX}")
    print(f"TASKS_LOAD_PLUGINS={TASKS_LOAD_PLUGINS}")
    print(f"TASKS_PLUGIN_DIRS={TASKS_PLUGIN_DIRS}")


@task()
def self_update(ctx: Context, git_remote=None, git_branch="main"):
    """Updates these scripts if they were cloned to ~/tasks or added as submodule"""
    folder = show_folder(ctx)
    if not git_remote:
        remote_line = ctx.run(f"git -C {folder} remote -v ").stdout.splitlines()[0]
        git_remote, *_ = re.split(r"\s+", remote_line)
    ctx.run(f"git -C {folder} pull {git_remote} {git_branch}", echo=True)


@task(autoprint=True)
def show_folder(
    ctx: Context,
):
    """Shows the folder where the taskfiles repo infers it's installed to"""
    # TODO: Check how this would work in a shiv/pex format
    folder = Path(__file__).resolve().parent
    return folder


def _get_plugin_dir() -> Path:
    import tasks

    return Path(tasks.__path__[0]) / "_plugins"


def _name_from_url(url: str) -> str:
    parsed = urlparse(url)
    path: str = parsed.path
    *_, name = path.split("/")
    name = name.replace("-", "_")
    return name


@task()
def install_plugin(ctx: Context, url_: List[str] = []):
    if not which("git"):
        sys.exit("Installing plugins requires git")
    if not url_:
        sys.exit("Please provide at least one URL")
    plugin_dir = _get_plugin_dir()
    for url in url_:
        name = _name_from_url(url)
        ctx.run(f"git clone {url} {plugin_dir / name}")


@task()
def uninstall_plugin(ctx: Context, name=None):
    ...


def _is_plugin(path: Path):
    if not path.is_dir():
        return False
    if path.name == "__pycache__":
        return False
    tasks_py = path / "tasks.py"
    if tasks_py.exists():
        return True
    package_marker = path / "__init__.py"
    if package_marker:
        return True
    return False


@task()
def list_plugins(ctx: Context, name=None):
    base: Path = _get_plugin_dir()

    for sub_dir in (f for f in base.glob("*") if _is_plugin(f)):
        print(sub_dir.name)


@task()
def update_plugin(ctx: Context, name=None):
    sys.exit("Not implemented")


@task()
def debugger(ctx: Context):
    breakpoint()  # noqa: T100
