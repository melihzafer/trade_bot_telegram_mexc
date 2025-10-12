"""
Logging module - Rich console + file logging.
"""
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table

from .config import LOG_DIR

# Rich console for pretty output
console = Console()

# Ensure log directory exists
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# Configure file logging
logging.basicConfig(
    filename=str(LOG_DIR / "runtime.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("mexc-bot")


def info(msg: str):
    """Log info message to both console and file."""
    log.info(msg)
    console.log(msg)


def warn(msg: str):
    """Log warning message to both console and file."""
    log.warning(msg)
    console.log(f"[yellow]{msg}[/yellow]")


def error(msg: str):
    """Log error message to both console and file."""
    log.error(msg)
    console.log(f"[red]{msg}[/red]")


def success(msg: str):
    """Log success message to both console and file."""
    log.info(msg)
    console.log(f"[green]{msg}[/green]")


def debug(msg: str):
    """Log debug message to file only."""
    log.debug(msg)
