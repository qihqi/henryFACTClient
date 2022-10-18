# -*- coding: utf-8 -*-

import base64
import os
import subprocess
import logging

from typing import List, cast

from henry import constants

_START_WEIGHT = 2
_MAX_WEIGHT = 7
_BASE = 11

def generate_checkcode(access_key: str) -> int:
    """
    Calculo mod 11
    return int
    """
    total = 0
    weight = _START_WEIGHT  # 2
    for item in reversed(access_key):
        total += int(item) * weight
        weight += 1
        if weight > _MAX_WEIGHT:
            weight = _START_WEIGHT
    mod = _BASE - total % _BASE
    if mod > 9:
        mod = _BASE - mod  # 11 -> 0, 10 -> 1
    return mod


def sign_xml(xml: str, p12filename: str, p12key: str) -> bytes:
    """
    Args:
        xml: is the content of the xml file
    """
    cmd = cast(List[str], [
        'java', '-jar',
        constants.SIGNER_PATH,
        xml,
        base64.b64encode(p12filename.encode('utf-8')).decode('ascii'),
        base64.b64encode(p12key.encode('utf-8')).decode('ascii'),
    ])
    print(' '.join(cmd))
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE)
    res = process.communicate()
    return res[0]
