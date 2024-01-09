def make_exe():
    dist = default_python_distribution()
    policy = dist.make_python_packaging_policy()
    python_config = dist.make_python_interpreter_config()
    # Enable loading local_tasks and plugins
    python_config.filesystem_importer = True
    python_config.run_module = "taskfiles"
    exe = dist.to_python_executable(
        name="tsk",
        packaging_policy=policy,
        config=python_config,
    )
    exe.add_python_resources(exe.pip_install(["invoke==2.2"]))
    # https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_managing_projects.html?highlight=VARS#defining-extra-variables-in-starlark-environment
    # This allows ot pass PACKAAGE='taskfiles[debug]' if a specific version
    # is required
    taskfile_package = VARS.get("PACKAGE", "taskfiles")
    exe.add_python_resources(
        exe.pip_install([taskfile_package],
        extra_envs={
            "PIP_FIND_LINKS": "dist/"
        })
    )
    return exe
def make_embedded_resources(exe):
    return exe.to_embedded_resources()
def make_install(exe):
    files = FileManifest()
    files.add_python_resource(".", exe)
    return files
def make_msi(exe):
    return exe.to_wix_msi_builder(
        "taskfiles",
        "Task automation in Python using Invoke",
        "1.0",
        "Nahuel Defossé"
    )
def register_code_signers():
    if not VARS.get("ENABLE_CODE_SIGNING"):
        return
register_code_signers()
register_target("exe", make_exe)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"], default=True)
register_target("msi_installer", make_msi, depends=["exe"])
resolve_targets()
