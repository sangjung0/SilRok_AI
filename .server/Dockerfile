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

# DOWNLOAD SCRIPT
ARG SCRIPT_PATH=/workspaces/script
RUN git clone --branch LID https://github.com/sangjung0/sjsh.git ${SCRIPT_PATH}
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
ENV PATH="${CONTAINER_HOME}/.local/bin:${PATH}"

# SETUP APP
ARG CONTAINER_WORK_DIR
ENV PYTHONPATH=${CONTAINER_WORK_DIR}
CMD ["bash", "-c", " \
    cd ${CONTAINER_WORK_DIR} \
    && /workspaces/script/sync_uv.sh ${CONTAINER_WORK_DIR} ${CONTAINER_HOME} ${CONTAINER_UV_GROUP} \
    && source ${CONTAINER_WORK_DIR}/.server/.env \
    && sudo chown -R ${CONTAINER_UID}:${CONTAINER_UID} ${CONTAINER_HOME} \
    && ${CONTAINER_WORK_DIR}/.venv/bin/python3 SilRok/main.py >> ${CONTAINER_WORK_DIR}/log/server.log 2>&1"]
