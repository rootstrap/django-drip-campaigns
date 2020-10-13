import re
import datetime

STRFDATETIME = re.compile('([dgGhHis])')


def STRFDATETIME_REPL(x):
    return '%({group})s'.format(group=x.group())


def process_regex(d):
    d = d.groupdict(0)
    if d['sign'] == '-':
        for k in 'hours', 'minutes', 'seconds':
            d[k] = '-' + d[k]
    d.pop('sign', None)
    return d


def get_flexible_regex(string):
    # This is the more flexible format
    d = re.match(
        r'^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?'
        r'((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?'
        r'((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?'
        r'((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?'
        r'((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$',
        string,
    )
    if not d:
        raise TypeError(
            "'{string}' is not a valid time interval".format(string=string)
            )
    d = d.groupdict(0)
    return d


def process_string(string):
    # This is the format we get from sometimes Postgres, sqlite,
    # and from serialization
    d = re.match(
        r'^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):'
        r'(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$',
        str(string),
    )
    if d:
        d = process_regex(d)
    else:
        d = get_flexible_regex(string)
    return datetime.timedelta(**dict(((k, float(v)) for k, v in d.items())))


def parse(string):
    """
    Parse a string into a timedelta object.
    """
    string = string.strip()

    if string == "":
        raise TypeError(
            "'{string}' is not a valid time interval".format(string=string)
            )
    return process_string(string)
