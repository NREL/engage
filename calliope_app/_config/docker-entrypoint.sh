#!/bin/bash

DIR=/docker-entrypoint.d

. /opsEnvInit/run_setup_env.sh

if [[ -d "$DIR" ]]
then
  /bin/run-parts --regex='^run.*' --verbose "$DIR"
fi

exec "$@"
