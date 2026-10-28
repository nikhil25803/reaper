"""Executable entry point for Reaper."""

from reaper.cli import app


def main() -> None:
    """Run the Reaper CLI."""
    app()


if __name__ == "__main__":
    main()
