
FROM python:3.12-slim-bookworm as app

# set environment variables
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PYTHONUNBUFFERED=TRUE

# install system dependencies
RUN apt-get update -y --fix-missing \
    && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libgmp3-dev \
    libz-dev \
    libreadline-dev \
    libncurses5-dev \
    gettext \
    postgresql-client \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libmetis-dev \
    coinor-cbc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
WORKDIR /www
COPY requirements.txt requirements-dev.txt /www/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt
# RUN pip install -r requirements.txt && pip install -r requirements-dev.txt
# Install calliope without dependencies, as already installed in requirements
# RUN pip install calliope==0.6.8 --no-deps && pip install flower>=1.1.0


# Install Geophires
RUN pip install git+https://github.com/NREL/GEOPHIRES-X.git#egg=geophires-x

# Install Calliope v0.7
RUN pip install git+https://github.com/jgu2/calliope.git@readd-links-yaml

# Uninstall git
RUN apt remove git -y && apt autoremove -y

COPY . .

RUN pip install -e .
