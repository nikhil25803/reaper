import subprocess
import sys

from typer.testing import CliRunner

from reaper import __version__
from reaper.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Reaper" in result.output
    assert "dead code detection and analysis" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == __version__ == "0.0.1"


def test_no_arguments_displays_help() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "--help" in result.output


def test_module_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "reaper.main", "--version"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == __version__
