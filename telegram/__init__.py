"""
Telegram integration module.

Components:
- collector: Multi-channel Telethon client for message collection
- parser: Signal extraction from raw messages
"""

from .collector import run_collector
from .parser import parse_message

__all__ = [
    "run_collector",
    "parse_message",
]
