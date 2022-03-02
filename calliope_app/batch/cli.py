"""
CLI command to solve model associated to Run instance.

Example
-------
engage solve-model --run-id=5 --user-id=1

"""
import logging
import sys

import click

from .handlers import ModelRunExecutor

logger = logging.getLogger(__name__)


@click.group()
def main():
    """Solving Engage models in commands"""
    return 0



@click.command()
@click.option(
    "--run-id",
    type=click.INT,
    required=True,
    help="The Run instance id"
)
@click.option(
    "--user-id",
    type=click.INT,
    required=True,
    help="The User instance id"
)
def solve_model(run_id, user_id):
    """Given a run id, run the Calliope model associated"""
    handler = ModelRunExecutor(run_id=run_id, user_id=user_id)
    handler.solve_model()
    logger.info("Model run & export success!")

main.add_command(solve_model)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
