"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """lazysequence."""


if __name__ == "__main__":
    main(prog_name="lazysequence")  # pragma: no cover
