FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-lc"]

# INSTALL DEPENDENCIES
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    git \
    sudo \
    zsh \
    curl \
    python3 \
    python3-pip \
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
COPY .devcontainer/sjsh /tmp/scripts
RUN chmod -R +x /tmp/scripts/*.sh

# ADD USER AND SETUP ZSH
ARG CONTAINER_USER
ARG CONTAINER_UID
ARG CONTAINER_HOME
RUN /tmp/scripts/add_user_and_setup_sudo.sh ${CONTAINER_USER} ${CONTAINER_UID}
RUN /tmp/scripts/setup_zsh.sh ${CONTAINER_USER} ${CONTAINER_UID} ${CONTAINER_HOME}

# INSTALL UV
RUN sudo -u ${CONTAINER_USER} curl -LsSf https://astral.sh/uv/install.sh | sudo -u ${CONTAINER_USER} sh
RUN sudo -u ${CONTAINER_USER} -H env PATH="${CONTAINER_HOME}/.local/bin:$PATH"

# INSTALL MECAB KOR
RUN /tmp/scripts/setup_mecab_kor.sh

# INSTALL UV
RUN sudo -u ${CONTAINER_USER} curl -LsSf https://astral.sh/uv/install.sh | sudo -u ${CONTAINER_USER} sh
RUN sudo -u ${CONTAINER_USER} -H env PATH="${CONTAINER_HOME}/.local/bin:$PATH"

# CLEANUP
RUN rm -rf /tmp/* || true

# FINALIZE
USER ${CONTAINER_USER}
