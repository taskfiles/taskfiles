import ast
import linecache
import os
import sys
from importlib import import_module
from pathlib import Path
from shlex import split
from subprocess import CalledProcessError, run
from typing import List

import invoke.exceptions
from invoke import Collection, Task

TASKS_KEEP_MODULE_NAME_PREFIX_ = os.environ.get("TASKS_KEEP_MODULE_NAME_PREFIX", "False")

try:
    TASKS_LOAD_PLUGINS = bool(ast.literal_eval(os.getenv("TASKS_LOAD_PLUGINS", "True")))
except Exception:
    TASKS_LOAD_PLUGINS = False

try:
    TASKS_PLUGIN_DIRS_ = os.getenv("TASKS_PLUGIN_DIRS", "")
    if isinstance(TASKS_PLUGIN_DIRS_, str):
        TASKS_PLUGIN_DIRS = TASKS_PLUGIN_DIRS_.split(":")
except Exception:
    TASKS_PLUGIN_DIRS = []


try:
    # Evaluate python expression, set to False on parsing error
    TASKS_KEEP_MODULE_NAME_PREFIX = ast.literal_eval(TASKS_KEEP_MODULE_NAME_PREFIX_)
except Exception:
    TASKS_KEEP_MODULE_NAME_PREFIX = False


def is_a_task_module(p: Path) -> bool:
    """Checks whether the file should be consider an task file"""
    if p.name.startswith("_"):
        return False
    if p.name == "tasks.py":
        # Avoid cyclic imports
        return False
    if p.name == "conftest.py":
        # Test code
        return False
    return True


def add_repo_root_to_sys_path() -> bool:
    """If running from a git repo, will find local_tasks.py in the toplevel"""
    try:
        top_level_git = run(split("git rev-parse --show-toplevel"), capture_output=True)
    except (CalledProcessError, FileNotFoundError):
        return False
    if top_level_git.returncode != 0:
        return False
    toplevel = top_level_git.stdout.strip().decode("utf-8")
    local_task_path = Path(toplevel) / "local_tasks.py"
    if not local_task_path.is_file():
        return False

    sys.path.insert(0, toplevel)
    return True


def import_with_exception_details(import_string, name=None):
    if not name:
        *_, name = import_string.split(".")
    try:
        return import_module(import_string)
    except Exception as error:
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        message = f'EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}'
        print(
            f"The module {name} has the following error: {error}. "
            f"(Debug info: {message}). "
            "You will not see any of the task defined in it until you fix the "
            "problem.",
            sep="\n",
            file=sys.stderr,
        )
        return None


def is_path_a_file(path: Path) -> bool:
    if path.is_file():
        return True
    if path.is_symlink() and path.readlink().is_file():
        return True
    return False


def is_path_a_folder(path: Path) -> bool:
    if path.name == "__pycache__":
        return False
    if path.is_dir():
        return True
    if path.is_symlink() and path.readlink().is_dir():
        return True
    return False


def find_and_import_tasks(
    where="__path__",
    keep_module_name_prefix=TASKS_KEEP_MODULE_NAME_PREFIX,
):
    """Autodiscovers any .py file in the tasks/ folder and adds it to the tasks
    collection. It can also split the task files into separate Collections.

    Parameters
    ----------
    where : str, optional
        The location where to find the modules, by default "__path__"
    keep_module_name_prefix : str, optional
        If "1" will split collections, by default
            os.environ.get("TASKS_KEEP_MODULE_NAME_PREFIX")

    Raises
    ------
    NotImplementedError
        When the where is not understood
    invoke.exceptions.Failure
        When the __path__ attribute fails to be spit (to be checked with PEX)
    """

    if isinstance(where, Path):
        mod_path_attribute = where.name
        path = where
    elif isinstance(where, str):
        mod_path_attribute = globals().get(where)
        try:
            path, *_ = mod_path_attribute
        except ValueError as err:
            msg = f"Failed to process tasks in {where}: {path}"
            raise invoke.exceptions.Failure(msg) from err
    else:
        msg = f"task discovery in {where} not implemented"
        raise NotImplementedError(msg)

    global_ns = Collection()

    def populate(
        module,
        name,
    ) -> bool:
        """
        Returns True if any successful additions happened
        """
        found = False
        if keep_module_name_prefix:
            ns = Collection.from_module(
                module,
                name,
            )
            global_ns.add_collection(coll=ns, name=name)
            found = True
        else:
            for _, task in module.__dict__.items():
                if not isinstance(task, Task):
                    continue
                global_ns.add_task(task)
                found = True
        return found

    task_files = [p for p in Path(path).glob("*.py") if is_a_task_module(p)]
    for task_file in task_files:
        name = task_file.stem
        import_string = f"tasks.{name}"
        module = import_with_exception_details(import_string=import_string, name=name)
        if not module:
            continue
        populate(module=module, name=name)

    # Finally try to import repo's top level task

    if add_repo_root_to_sys_path():
        name = "local_tasks"
        try:
            module = import_module(name)
        except Exception as error:
            print(
                f"The module {name} has the following error: {error}."
                "You will not see any of the task defined in it until you fix the "
                "problem.",
                sep="\n",
                file=sys.stderr,
            )
        populate(module, name=name)
    # Try to load plugins
    if TASKS_LOAD_PLUGINS:
        for plugin_dir in TASKS_PLUGIN_DIRS:
            path = Path(plugin_dir)
            if path.is_absolute() and path.exists():
                print(f"Not implemented yet. Skipping {plugin_dir}")
                continue
        internal_plugins = where / "_plugins"
        is_package = (internal_plugins / "__init__.py").is_file()
        if internal_plugins.exists() and is_package:
            # Allow core to list plugin tasks
            TASKS_PLUGIN_DIRS.append(str(internal_plugins))
            to_load: List[Path] = [
                elem
                for elem in internal_plugins.glob("*")
                if not elem.name == "__init__.py"
            ]
            for plugin in to_load:
                if is_path_a_file(plugin) and plugin.name.endswith(".py"):
                    name = plugin.name.replace(".py", "")
                    import_string = f"tasks._plugins.{name}"
                    module = import_with_exception_details(
                        import_string=import_string, name=name
                    )
                    if not module:
                        continue
                    populate(module=module, name=name)
                elif is_path_a_folder(plugin):
                    name = f"tasks._plugins.{plugin.name}"
                    module = import_with_exception_details(name, name=name)
                    if not module:
                        print(f"Skipping {import_string}")
                        continue
                    any_task = populate(module=module, name=name)
                    if not any_task:
                        # It's not a package but a collection of files
                        sys.path.append(plugin)
                        for py_file in plugin.glob("*.py"):
                            name = py_file.name.replace(".py", "")
                            import_string = f"tasks._plugins.{plugin.name}.{name}"
                            module = import_with_exception_details(
                                import_string=import_string, name=name
                            )
                            if not module:
                                continue
                            populate(module=module, name=name)

    return global_ns
