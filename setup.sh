#!/bin/sh
# For testing on Mac M1 use the following command:
# docker run --platform linux/amd64 --rm -ti -v $PWD:/tasks -w / alpine sh  -c 'sh /tasks/setup.sh; sh'
# Bootstrapping script
set -x

IN_DOCKER=$(test -f /.dockerenv && echo 1 || echo 0)
if cat /etc/os-release | grep -i alpine 1>/dev/null; then
    ALPINE=1
else
    ALPINE=0
fi

# echo $IN_DOCKER $ALPINE
setup_alpine() {
    echo "Setting up alpine"
    apk add gcompat python3 gettext bash curl git
    python3 -m ensurepip
    # Hunter can be activated by PYTHONHUNTER="module_sw='tasks'"
    python3 -m pip install invoke pdbpp hunter
}

if [ $ALPINE = "1" ]; then
    setup_alpine
else
    echo "This setup only supports Alpine at the moment"
    exit 1
fi
