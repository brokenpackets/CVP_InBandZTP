# -*- coding: utf-8 -*-

from distutils.util import strtobool
from os import getenv

LOOPBACK = "127.0.0.1"


def _str2bool(string: str) -> bool:
    return bool(strtobool(string))


def connection_details():
    return {
        "username": getenv("CVPIBZTP_USERNAME"),
        "password": getenv("CVPIBZTP_PASSWORD"),
        "server": getenv("CVPIBZTP_SERVER", LOOPBACK),
        "verify": _str2bool(getenv("CVPIBZTP_VERIFY", "True")),
    }
