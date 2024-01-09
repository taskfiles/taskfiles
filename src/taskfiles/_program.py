import logging
import os

from invoke import Program

from taskfiles import __version__

from . import get_root_ns


class TaskfilesProgram(Program):
    def __init__(
        self,
        # version: str | None = None,
        # namespace: Collection | None = None,
        # name: str | None = None,
        # binary: str | None = None,
        # loader_class: type[Loader] | None = None,
        # executor_class: type[Executor] | None = None,
        # config_class: type[Config] | None = None,
        # binary_names: List[str] | None = None,
    ) -> None:
        self.configure_logging()
        ns = get_root_ns()
        super().__init__(
            # loader_class,
            # executor_class,
            # config_class,
            name="Taskfiles",
            binary="taskf[iles]",
            binary_names=["taskfiles", "taskf"],
            version=__version__,
            namespace=ns,
        )

    def configure_logging(self):
        logging.basicConfig(level=os.environ.get("TASKS_LOGLEVEL", "INFO"))
