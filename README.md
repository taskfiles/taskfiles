# Automation Scripts based on Invoke
- [Automation Scripts based on Invoke](#automation-scripts-based-on-invoke)
  - [Installation](#installation)
    - [Global install](#global-install)
      - [Generic (as a CICD helper)](#generic-as-a-cicd-helper)
      - [With brew](#with-brew)
      - [With pipx](#with-pipx)
      - [With pip](#with-pip)
    - [As a submodule](#as-a-submodule)
  - [Description](#description)
  - [Usage](#usage)
  - [Autocompletion](#autocompletion)
    - [Bash](#bash)
    - [Zsh](#zsh)
    - [Fish](#fish)
  - [Plugins](#plugins)
  - [Setup](#setup)
    - [Debugging](#debugging)
  - [Environment Variables](#environment-variables)
  - [`TASKS_KEEP_MODULE_NAME_PREFIX`](#tasks_keep_module_name_prefix)
  - [Self Tests](#self-tests)
    - [Testing with docker multi-platform support](#testing-with-docker-multi-platform-support)
    - [Cross platform testing with buildx](#cross-platform-testing-with-buildx)

## Installation

### Global install

#### Generic (as a CICD helper)

1. Ensure you have Python 3 (3.8+) and [invoke](https://pyinvoke.org)
   - Python3 can be installed with `apt`, `apk`, `nix`, `dnf` depending on the host operating system.
   - `invoke` is a Python library, and can be installed with
     `python3 -m ensurepip; python3 -m pip install invoke`
2. Clone or submodule this repo as `~/tasks/` (`$HOME/tasks`). Symlinking it is also fine.
3. Run `inv -l` to verify the installation.

#### With brew

1. To install [`inv`](https://pyinvoke.org) globally in OSX:
   `brew install pyinvoke`
1. Clone or submodule this repo as `~/tasks/` (`$HOME/tasks`). Symlinking it is also fine.
1. Run `inv -l` to verify the installation.

#### With [pipx](https://github.com/pypa/pipx)

1. `pipx install invoke`
1. Clone or submodule this repo as `~/tasks/` (`$HOME/tasks`). Symlinking it is also fine.
1. Run `inv -l` to verify the installation.

#### With pip

1. To install invoke locally as a user, not recommended because this method doesn't have a straight-forward upgrade mechanism.
   `pip install --user invoke`

1. Clone or submodule this repo as `~/tasks/` (`$HOME/tasks`). Symlinking it is also fine.
1. Run `inv -l` to verify the installation.

### As a submodule

1. Ensure python3 has invoke (if you're using poetry, pipenv, hatch, poetry), add it as a development dependency (or install it globally)
1. In your repo `cd (git rev-parse --show-toplevel) &&  git submodule add https://github.com/taskfiles/taskfiles.git`
1. Run `inv -l` and ensure the task are available.


## Description

This repository holds a set of automation scripts for
some common tasks like downloading static binaries binaries, shell setup (for VMs or SSH hosts),
docker image handling, local kubernetes development, git aliases.

It's not (yet) mean to be used as a Python package (in spite of having a [pyproject.toml](pyproject.toml)).

This repository can be used in your $HOME, or as part of another specific to a repo as (as a submodule named `tasks`).
This name is required to be tasks `tasks` for [pyivoke](http://pyinvoke.org) to find the tasks. This will trigger
the code in `__init__.py` and try to import all the files in this repo. It will also look for the `_plugin` folder.

Plugin support works for simple use cases. This will be improved in the future.

A list of tasks can be shown with the command `inv -l` (`inv list-tasks`)

![Example](docs/img/inv-list.svg)

<small>This recording was done with `termtosvg`</small>

## Usage

For better experience in interactive sessions ensure you have enabled [autcompletion](#autocompletion).

To list available tasks run `inv -l`.

For example, to run the task `install-fzf`, just run `inv install-fzf`.


## Autocompletion

To enable auto-completion, follow these instructions according to your shell (run `echo $SHELL` to find out which one you're using).
Make sure to restart the shell after the changes.

### Bash

`inv --print-completion-script bash >> ~/.bashrc`

### Zsh

`inv --print-completion-script zsh >> ~/.zshrc`

### Fish

`inv --print-completion-script fish > ~/.config/fish/completions/inv.fish`

## Plugins

This project supports plugins in the `_plugins` directory.

A plugin is a collection of files.

## Setup

This repo should be *sub-moduled* at the top of the repo and the
`invoke` command should be available system-wide, although installing
it in the repo where sub-moduled should be fine.


### Debugging

If `breakpoint()` is not enough, we encourage to
add the `hunter` python library to trace/debug to your `invoke`
python environment to trace execution. It can be activated
with the PYTHONHUNTER environment variable.

```
PYTHONHUNTER='module="tasks"' inv -l
```

Visualizing variables:

```bash
PYTHONHUNTER='module__contains="my_file", actions=[CodePrinter, VarsSnooper]' inv -l
```


Debugging import issues with `local_tasks.py` in your repo:


```bash
 PYTHONHUNTER='module__contains="_discovery", actions=[CodePrinter, VarsSnooper]' inv -l
```


## Environment Variables

Some of this variables can be set in .envrc files [direnv](https://direnv.net) or
`.env` (note that this task will not auto-load the later and need to be sourced first)

## `TASKS_KEEP_MODULE_NAME_PREFIX`

Keeps the file name (module) as a prefix. When using `local_tasks` enables
`inv -l local_tasks`.

```
inv -l local-tasks
Available 'local-tasks' tasks:

  .create-local-dev-cluster                          Creates a local development cluster
  .deploy-demo-inference-service                     Deploys the demo inference service
  .send-http-inference                               More interesting stuff
  ```

## Self Tests

There's some self-tests bundled in the project. As of now, the binary downloader part of the [setup.py](setup.py) task modules
is the only part tested.

These can be triggered from:

```bash
docker compose -f _tests/compose.yaml run --rm test
```

### Testing with docker multi-platform support

On ARM Macs, run:

```bash
PLATFORM=linux/amd64 docker compose -f _tests/compose.yaml run --rm test inv install-k9s
```

Note that Docker can hold only a tag per platform, if you see a error message like
`Error response from daemon: conflict: unable to remove repository reference "python:3.11" (must force) - container 6a363e1c1b6c is using its referenced image ee16e609eb10`, run the following  command to clear the tag:

```bash
docker image rm -f python:3.11
```

### Cross platform testing with buildx

```bash
docker build --platform linux/amd64  -t inv . && docker run --platform linux/amd64 -v .:/tasks --rm -ti  inv inv install-all
```
