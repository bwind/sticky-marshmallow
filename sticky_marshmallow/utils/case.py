import re


def camel_case(s):
    camel_cased = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), s)
    return camel_cased[0].upper() + camel_cased[1:]


def snake_case(s):
    snake_cased = re.sub(r"([A-Z])", lambda m: "_" + m.group(1).lower(), s)
    return snake_cased.strip("_")
