FROM python:3.12-slim-bullseye as app

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
    wget \
    git \
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

# Install python packages
WORKDIR /www
COPY requirements.txt requirements-dev.txt /www/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

# Install Geophires
RUN pip install git+https://github.com/NREL/GEOPHIRES-X.git#egg=geophires-x

# Install Calliope v0.7
RUN pip install git+https://github.com/calliope-project/calliope.git@v0.7.0.dev3

COPY . .

RUN pip install -e .
