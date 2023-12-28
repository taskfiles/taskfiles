import ast
import ipaddress
import os
import re
import sys
from shutil import which
from urllib.parse import urlparse

from invoke import Context, Result, task


@task(autoprint=True)
def ssh_host(ctx: Context):
    return ctx.run(
        'grep -h "^Host" ~/.ssh/config ~/.ssh/config.d/* | '
        r"grep -v '\*' | sed -e s/Host//g | awk '{ print $1}'",
        hide="out",
        pty=True,
    ).stdout


@task()
def create_ssh_key_private_rsa(ctx: Context, comment=None, name="key"):
    """
    Creates a ssh key-pair with private RSA.
    """
    if not comment:
        comment = "taskfiles.automation"
    ctx.run(f"ssh-keygen -t rsa -b 4096 -C '{comment}' -f {name}.pem")
    ctx.run(f"ssh-keygen -p -N '' -m pem -f {name}.pem")


SSHUTTLE_REMOTE = os.environ.get("SSHUTTLE_REMOTE")
SSHUTTLE_TARGETS = re.split(r"[\s+,]", os.environ.get("SSHUTTLE_TARGETS", ""))
sshuttle_reconnect_ = os.environ.get("SSHUTTLE_RECONNECT", "True")

try:
    SSHUTTLE_RECONNECT = ast.literal_eval(sshuttle_reconnect_)
except:  # noqa: E722
    SSHUTTLE_RECONNECT = True


def is_valid_ip(address):
    try:
        ipaddress.ip_network(address, strict=False)
        return True
    except ValueError:
        return False


@task()
def get_A_records(ctx: Context, domain: str) -> list[str]:  # noqa: N802
    """Uses dig to get the IP addresses"""
    if domain.startswith("http"):
        domain = urlparse(domain).hostname
    all_records = ctx.run(f"dig +short A {domain}", hide=True).stdout.splitlines()
    ip_records = [rec for rec in all_records if is_valid_ip(rec)]
    return ip_records


@task(autoprint=True)
def expand_lb_domain(ctx: Context, domain: str) -> str:
    """Uses dig to get the IP addresses"""
    records = get_A_records(ctx, domain=domain)
    return "\n".join(records)


OP_PASSWORD_NAME_SUDO = os.getenv("OP_PASSWORD_NAME_SUDO", None)


@task(
    help={
        "remote": "Host to use as bastion, defaults to $SSHUTTLE_REMOTE",
        "target_": "Host to be reached though the remote, can be passed multiple times"
        " (comma separated under $SSHUTTLE_TARGETS)",
        "daemon": "Run in the background",
        "op_password_name_sudo": "If the op command line is available , use op to get the"
        " password",
        "reconnect": f"Reconnect if sshuttle fails, (default {SSHUTTLE_RECONNECT}) "
        "defined in $SSHUTTLE_RECONNECT.",
    }
)
def sshuttle(
    ctx: Context,
    remote=SSHUTTLE_REMOTE,
    target_: list[str] = [],
    op_password_name_sudo=OP_PASSWORD_NAME_SUDO,
    daemon=False,
    reconnect=SSHUTTLE_RECONNECT,
):
    """Runs sshuttle to reach hosts that are behind a firewall or a different network"""
    while True:
        target_ = target_ or SSHUTTLE_TARGETS
        hosts = []
        if not remote:
            sys.exit("No remote host defined. Can be an argument or $SSHUTTLE_REMOTE")

        for target in target_:
            if not is_valid_ip(target):
                ips = get_A_records(ctx, target)
                hosts.extend(ips)
            else:
                hosts.append(target)

        if not hosts:
            sys.exit(f"No targets defined (tried {remote})")
        prefix = ""
        if op_password_name_sudo:
            if not which("op"):
                sys.exit("1Password CLI not found. Skipping...")
            else:
                prefix = (
                    f"""
                    {prefix} echo "$(op item get '{op_password_name_sudo}' \
                    --field password)" | sudo -S'
                    """
                ).strip()

        targets = " ".join(hosts)
        if not targets:
            sys.exit("No targets could be resolved.")
        args = ""
        if daemon:
            args = f"{args} -D"
        sshuttle_: Result = ctx.run(
            f"{prefix} sshuttle -r {remote} {targets} {args}",
            # in_stream=None,
            pty=True,
            warn=True,
        )
        print(f"sshuttle process exited (code: {sshuttle_.return_code})", file=sys.stderr)
        if not sshuttle_.ok and not reconnect:
            return
