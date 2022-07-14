import datetime
import re
from typing import Dict, Match, Union


def process_regex(matches: Match[str]) -> Dict[str, Union[str, int]]:
    matches_dict = matches.groupdict(0)
    if matches_dict["sign"] == "-":
        for k in "hours", "minutes", "seconds":
            matches_dict[k] = "-" + str(matches_dict[k])
    matches_dict.pop("sign", None)
    return matches_dict


def get_flexible_regex(string: str) -> Dict[str, Union[str, int]]:
    """
    Matches a string using a more flexible regex expression for parsing
    it to timedelta object.
    """
    matches = re.match(
        r"^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?"
        r"((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?"
        r"((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?"
        r"((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?"
        r"((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$",
        string,
    )
    if not matches:
        raise TypeError("'{string}' is not a valid time interval".format(string=string))
    flexible_regex = matches.groupdict(0)
    return flexible_regex


def process_string(string: str) -> datetime.timedelta:
    """
    Process a string into a timedelta object, using a standard format used by
    Postgres, sqlite, or from serialization. Or a flexible regex expression
    if the standard form is not enough.
    """
    matches = re.match(
        r"^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):"
        r"(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$",
        str(string),
    )
    if matches:
        formated_dict = process_regex(matches)
    else:
        formated_dict = get_flexible_regex(string)
    return datetime.timedelta(**dict(((k, float(v)) for k, v in formated_dict.items())))


def parse(string: str) -> datetime.timedelta:
    """
    Parse a string into a timedelta object.
    """
    string = string.strip()

    if string == "":
        raise TypeError("'{string}' is not a valid time interval".format(string=string))
    return process_string(string)
