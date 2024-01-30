FROM python:3.8-slim-bullseye as app

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
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# build GLPK 4.65 solver
WORKDIR /solvers
RUN wget --no-check-certificate https://ftp.gnu.org/gnu/glpk/glpk-4.65.tar.gz
RUN tar -zxf glpk-4.65.tar.gz
WORKDIR /solvers/glpk-4.65
RUN ./configure \
	&& make \
	&& make check \
	&& make install \
	&& make distclean \
	&& ldconfig \
    # Cleanup
	&& rm -rf /solvers/glpk-4.65.tar.gz \
	&& apt-get clean

# install python packages
WORKDIR /www
COPY requirements.txt requirements-dev.txt /www/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

# Install calliope without dependencies, as already installed in requirements
# RUN pip install calliope==0.6.8 --no-deps
RUN pip install git+https://github.com/calliope-project/calliope.git@refs/pull/517/head
RUN pip install flower>=1.1.0

COPY . .

RUN pip install -e .
