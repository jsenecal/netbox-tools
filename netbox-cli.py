import click
import click_log
import logging
logger = logging.getLogger(__name__)
click_log.basic_config(logger)

@click.command()
@click_log.simple_verbosity_option(logger)
def cli():
    logger.info("Dividing by zero.")

    try:
        1 / 0
    except:
        logger.error("Failed to divide by zero.")


if __name__ == '__main__':
    cli()