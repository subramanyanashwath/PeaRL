"""PeaRL command-line entry point."""

from __future__ import annotations

import typer

from pearl import __version__

app = typer.Typer(
    name="pearl",
    help="Environment-centric experimentation and improvement for AI agents.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pearl {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the PeaRL version and exit.",
    ),
) -> None:
    """Inspect and run PeaRL experiments."""


if __name__ == "__main__":  # pragma: no cover
    app()
