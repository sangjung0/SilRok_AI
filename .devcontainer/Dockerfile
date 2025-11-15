FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-lc"]

# INSTALL DEPENDENCIES
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    git sudo zsh curl python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# INSTALL ADDITIONAL DEPENDENCIES
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    # LIA
    ffmpeg \
    # setup_mecab_kor.sh dependencies
    autoconf automake build-essential libtool \
    # pyannote
    libportaudio2 \
    # graphviz
    openjdk-17-jdk graphviz \
    && rm -rf /var/lib/apt/lists/*

# LOAD SCRIPT
ARG SCRIPT_PATH=/tmp/scripts
COPY .devcontainer/sjsh ${SCRIPT_PATH}
RUN chmod -R +x ${SCRIPT_PATH}/*.sh

# ADD USER AND SETUP ZSH
ARG CONTAINER_USER
ARG CONTAINER_UID
ARG CONTAINER_HOME
RUN ${SCRIPT_PATH}/add_user_and_setup_sudo.sh ${CONTAINER_USER} ${CONTAINER_UID}
RUN ${SCRIPT_PATH}/setup_zsh.sh ${CONTAINER_USER} ${CONTAINER_UID} ${CONTAINER_HOME}

# INSTALL MECAB KOR
RUN ${SCRIPT_PATH}/setup_mecab_kor.sh

# CLEANUP
RUN rm -rf /tmp/* || true

# SWITCH USER
USER ${CONTAINER_USER}

# INSTALL UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="${CONTAINER_HOME}/.uv/bin:$PATH"
