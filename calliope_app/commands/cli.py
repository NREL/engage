"""Console script for ncloud."""
import sys
import click

from .solve_model import solve_model


@click.group()
def main():
    """Solving Engage models in commands"""
    return 0


main.add_command(solve_model)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
