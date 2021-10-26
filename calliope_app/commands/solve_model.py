import logging
import os

import click
from calliope import Model

logger = logging.getLogger(__name__)


@click.command()
@click.argument("config-file")
@click.option(
    "--outputs",
    type=click.Path(),
    required=True,
    help="The output directory of model run"
)
def solve_model(config_file, outputs):
    """Run Calliope model with given config file"""
    # Solve Calliope model
    try:
        logger.info("Engage solving model - %s", config_file)
        model = Model(config_file)
        model.run()
        logger.info("Model run success - %s", config_file)
    except Exception as err:
        logger.error("Failed to solve model - %s", config_file)
        logger.error(str(err))
        return

    # Export Calliope model run results in CSV
    model_outputs = os.path.join(outputs, "model_outputs")
    if os.path.exists(model_outputs):
        shutil.rmtree(model_outputs)
        os.makedirs(model_outputs)

    try:
        logger.info("Exporting model results in CSV - %s", config_file)
        model.to_csv(model_outputs)
    except Exception as err:
        logger.error("Failed to export CSV results - %s", )

    # Export HTML plots
    plot_file = os.path.join(outputs, "model_plots.html")
    model.plot.summary(to_file=plot_file)

    logger.info("Model run & export success!")
