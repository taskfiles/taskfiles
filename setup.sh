#!/bin/sh
# For testing on Mac M1 use the following command:
# docker run --platform linux/amd64 --rm -ti -v $PWD:/tasks -w / alpine sh  -c 'sh /tasks/setup.sh; sh'
# Bootstrapping script
# set -x
{
    OS_TYPE="unknown"
    IN_DOCKER=$(test -f /.dockerenv && echo 1 || echo 0)

    if cat /etc/os-release | grep -i alpine 1>/dev/null; then
        OS_TYPE="alpine"
    fi

    if cat /etc/os-release | grep -i ubuntu 1>/dev/null; then
        OS_TYPE="ubuntu"
    fi

    # echo $IN_DOCKER $ALPINE
    setup_alpine() {
        echo "Setting up alpine"
        apk add gcompat python3 gettext bash curl git
        python3 -m ensurepip
        # Hunter can be activated by PYTHONHUNTER="module_sw='tasks'"
        python3 -m pip install invoke pdbpp hunter
    }

    setup_ubuntu() {
        set -ex
        # python3 present,
        # ensurepip not available
        echo "Set up Ubuntu"
        workdir=$(mktemp --directory)
        if ! python3 -m pip >/dev/null 2>/dev/null; then
            echo "Installing pip"
            wget https://bootstrap.pypa.io/get-pip.py -O $workdir/get-pip.py
            python3 $workdir/get-pip.py
        fi
        if ! type "inv" > /dev/null; then
            python3 -m pip install invoke
            echo "Installing invoke"
        fi

        rm -rf $workdir
    }

    if [ $OS_TYPE = "alpine" ]; then
        setup_alpine
    elif [ $OS_TYPE = "ubuntu" ]; then
        setup_ubuntu
    else
        echo "Doesn't support your operting system"
        exit 1
    fi
}
