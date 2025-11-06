"""
Validation utilities for Pydantic models.
"""

import re
from datetime import timedelta
from typing import Callable, List, Tuple, Union


def parse_duration_string(duration_str: str) -> Union[timedelta, None]:
    """
    Parse a duration string in readable format to timedelta.

    Supports multiple formats:
    - "140s" or "140seconds" -> timedelta(seconds=140)
    - "2h" or "2hours" -> timedelta(hours=2)
    - "30m" or "30minutes" -> timedelta(minutes=30)
    - "1d" or "1days" -> timedelta(days=1)
    - "1:30" -> timedelta(hours=1, minutes=30)
    - "1:30:45" -> timedelta(hours=1, minutes=30, seconds=45)
    - "140" -> timedelta(seconds=140) (number only)

    Args:
        duration_str: Duration string to parse

    Returns:
        Parsed timedelta or None if cannot be parsed
    """
    if not duration_str or not isinstance(duration_str, str):
        return None

    # Clean and normalize the string
    v = duration_str.strip().lower()

    # Patterns for different formats
    patterns: List[Tuple[str, Callable[..., timedelta]]] = [
        (r"(\d+)s(?:econds?)?", lambda x: timedelta(seconds=int(x))),
        (r"(\d+)m(?:in(?:utes?)?)?", lambda x: timedelta(minutes=int(x))),
        (r"(\d+)h(?:ours?)?", lambda x: timedelta(hours=int(x))),
        (r"(\d+)d(?:ays?)?", lambda x: timedelta(days=int(x))),
        (
            r"(\d+):(\d+):(\d+)",
            lambda h, m, s: timedelta(hours=int(h), minutes=int(m), seconds=int(s)),
        ),
        (r"(\d+):(\d+)", lambda h, m: timedelta(hours=int(h), minutes=int(m))),
    ]

    for pattern, converter in patterns:
        match = re.match(pattern, v)
        if match:
            return converter(*match.groups())

    # If no pattern matches, try parsing as number of seconds
    try:
        seconds = float(v)
        return timedelta(seconds=seconds)
    except ValueError:
        pass

    # If cannot be parsed, return None
    return None


def duration_validator(v: Union[str, timedelta, None]) -> Union[timedelta, None]:
    """
    Pydantic validator for duration fields.

    Args:
        v: Value to validate (can be str, timedelta, or None)

    Returns:
        timedelta or None
    """
    if v is None:
        return None
    if isinstance(v, timedelta):
        return v
    if isinstance(v, str):
        return parse_duration_string(v)

    return v

