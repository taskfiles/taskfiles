FROM python:3.11-slim
# 👇 keep these lines together
ARG COMMIT_ID=unknown \
    GIT_BRANCH=unknown \
    CHECKOUT_STATUS=unknown \
    CUSTOM_INSTALL_SCRIPT=true

ENV COMMIT_ID=${COMMIT_ID} \
    GIT_BRANCH=${GIT_BRANCH} \
    CHECKOUT_STATUS=${CHECKOUT_STATUS} \
    CUSTOM_INSTALL_SCRIPT=${CUSTOM_INSTALL_SCRIPT}
# 👆 keep these lines together

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN true && \
    apt-get update && \
    apt-get --no-install-recommends -yqq install git-core gettext && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# hadolint ignore=DL3013
RUN pip install --no-cache-dir "invoke>2.0,<3.0" hunter pdbpp

ENV PATH=$HOME/.local/bin:$PATH

COPY . /tasks/
