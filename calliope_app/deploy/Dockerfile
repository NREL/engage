FROM python:3.8-slim-bookworm as fakemac
WORKDIR /fakemac
RUN apt-get update -y --fix-missing && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    sudo
RUN git clone https://github.com/kumina/fakemac \
    && cd fakemac \
    && make \
    && sudo make install \
    && rm -rf ../fakemac

FROM python:3.8-slim-bookworm as app

# set environmental variables
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PYTHONUNBUFFERED=TRUE

# RUN addgroup --system django && adduser --system --ingroup django django
RUN mkdir /www /data /static && mkdir -p /opt/python/log
# RUN chown django:django /www
# RUN chown django:django /data
# RUN chown django:django /opt/python/log
# RUN chown django:django /static

# mount volume
VOLUME /static

# install system dependencies
RUN apt-get update -y --fix-missing && apt-get upgrade -y\
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgmp3-dev \
        libz-dev \
        libreadline-dev \
        libncurses5-dev \
        postgresql-client \
        python3-dev \
        supervisor \
        netcat-openbsd \
        git \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Solvers
WORKDIR /solvers
COPY solvers/ /solvers

# Solver: GLPK 4.65
RUN cd /solvers && tar -zxvf glpk-4.65.tar.gz
WORKDIR /solvers/glpk-4.65
RUN ./configure \
	&& make \
	&& make check \
	&& make install \
	&& make distclean \
	&& ldconfig \
    # Cleanup
	&& rm -rf /user/local/glpk-4.65.tar.gz \
	&& apt-get clean

RUN apt-get purge -y wget

# Solver: XPRESS
ENV XPRESSDIR=/usr/local/xpressmp
ENV XPRESS=/usr/local/xpressmp/bin

ENV LD_LIBRARY_PATH=${XPRESSDIR}/lib:${LD_LIBRARY_PATH}
ENV SHLIB_PATH=${XPRESSDIR}/lib:${SHLIB_PATH}
ENV LIBPATH=${XPRESSDIR}/lib:${LIBPATH}
ENV PYTHONPATH=${XPRESSDIR}/lib:${PYTHONPATH}

ENV CLASSPATH=${XPRESSDIR}/lib/xprs.jar:${CLASSPATH}
ENV CLASSPATH=${XPRESSDIR}/lib/xprb.jar:${CLASSPATH}
ENV CLASSPATH=${XPRESSDIR}/lib/xprm.jar:${CLASSPATH}
ENV PATH=${XPRESSDIR}/bin:${PATH}

RUN cd /solvers && tar -xvf xp8.0.4_linux_x86_64_setup.tar
RUN cd /solvers && bash -c '/bin/echo -e "s\n\nn\nn\ny"' | sh ./install.sh

# Software licenses
COPY _config/docker-entrypoint.sh /
RUN chmod 755 /docker-entrypoint.sh

RUN mkdir -p /docker-entrypoint.d
COPY _config/docker-entrypoint.d/* /docker-entrypoint.d/
RUN chmod 755 /docker-entrypoint.d/*

RUN mkdir -p /opsEnvInit
COPY _config/opsEnvInit/* /opsEnvInit/
RUN chmod 755 /opsEnvInit/*

COPY _config/default.conf /etc/nginx/site-enabled/

WORKDIR /www/

# python packages
COPY requirements.txt /www/
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt
RUN pip install calliope==0.6.8 --no-deps
RUN pip install gunicorn==20.1.0

COPY ./calliope-files/preprocess/sets.py /usr/local/lib/python3.8/site-packages/calliope/preprocess/sets.py
COPY ./calliope-files/preprocess/constraint_sets.py /usr/local/lib/python3.8/site-packages/calliope/preprocess/constraint_sets.py
COPY ./calliope-files/config/defaults.yaml /usr/local/lib/python3.8/site-packages/calliope/config/defaults.yaml
COPY ./calliope-files/backend/pyomo/constraints/costs.py /usr/local/lib/python3.8/site-packages/calliope/backend/pyomo/constraints/costs.py
COPY ./calliope-files/backend/pyomo/model.py /usr/local/lib/python3.8/site-packages/calliope/backend/pyomo/model.py
COPY ./calliope-files/backend/pyomo/util.py /usr/local/lib/python3.8/site-packages/calliope/backend/pyomo/util.py
# For calliope==0.6.8 works with HiGHS solver with pyomo==6.7.0
COPY ./calliope-files/backend/run.py /usr/local/lib/python3.8/site-packages/calliope/backend/run.py

# operations
ARG LOG_DIR=/opt/python/log
RUN mkdir -p $LOG_DIR
RUN touch $LOG_DIR/supervisord.log $LOG_DIR/celery_worker.log $LOG_DIR/celery_flower.log
RUN chmod 777 $LOG_DIR/supervisord.log $LOG_DIR/celery_worker.log $LOG_DIR/celery_flower.log

COPY . .

RUN pip install -e .

# RUN chown -R django:django /www
# RUN chown -R django:django /data
# RUN chown -R django:django /opt/python/log
# RUN chown -R django:django /static

# RUN chmod -R +x deploy/
# RUN chmod -R 744 /www
# RUN chmod -R 744 /data
# RUN chmod -R 744 /opt/python/log
# RUN chmod -R 744 /static

# RUN mkdir -p /usr/local/xpressmp/bin/ && touch /usr/local/xpressmp/bin/xpauth.xpr && chown -Rv django:django /usr/local/xpressmp/bin/
RUN mkdir -p /usr/local/xpressmp/bin/ && touch /usr/local/xpressmp/bin/xpauth.xpr
COPY --from=fakemac /usr/bin/fakemac /usr/bin/
COPY --from=fakemac /usr/lib/libfakemac.so /usr/lib/

# USER django

ENTRYPOINT ["/docker-entrypoint.sh"]
