""" Miscellanous stuff"""
from __future__ import division
from __future__ import print_function

from builtins import str
from builtins import zip
from builtins import map
import re
from decimal import Decimal
from henry.hack import fix_id_error


def id_type(uid):
    if uid == 'NA' or uid.startswith('9999'):
        return '07'  # General

    uid = fix_id(uid)
    if len(uid) == 10:
        return '05'  # cedula
    elif len(uid) == 13:
        return '04'  # RUC
    else:
        print('error!! uid {} with length {}'.format(uid, len(uid)))
    return '07'


def fix_id(uid):
    uid = fix_id_error(uid)
    if uid == 'NA':
        return '9' * 13  # si es consumidor final retorna 13 digitos de 9
    uid = re.sub('[^\d]', '', uid)
    if not validate_uid_and_ruc(uid):
        return '9' * 13
    return uid


def abs_string(string):
    if string.startswith('-'):
        return string[1:]
    return string

def validate_ruc(uid):
    if uid[2] == '9': # ruc of private parties
        coef = [4, 3, 2, 7, 6, 5, 4, 3, 2]
        the_sum = sum(x * y for x, y in zip(coef, list(map(int, uid[:9]))))
        the_sum = 11 - the_sum % 11
        if the_sum > 10:
            the_sum -= 10
        return int(uid[9]) == the_sum
    elif uid[2] == '6': # ruc of public parties
        coef = [3, 2, 7, 6, 5, 4, 3, 2]
        the_sum = sum(x * y for x, y in zip(coef, list(map(int, uid[:8]))))
        the_sum = 11 - the_sum % 11
        if the_sum > 10:
            the_sum -= 10
        return int(uid[8]) == the_sum
    else: # ruc of persons
        return validate_cedula(uid[:10])

def validate_cedula(uid):
    first_digits = int(uid[:2])
    if first_digits < 1 or first_digits > 24:
        return False

    sum_even = 0
    sum_old = 0
    for i, x in enumerate(uid):
        d = int(x)
        if i % 2 == 1:  # it is 0 indexed, so odd positions have even index
            if i == 9:
                continue
            sum_even += d
        else:
            d = (d * 2)
            if d > 9:
                d -= 9
            sum_old += d
    sum_all = sum_even + sum_old
    sum_first_digit = str(sum_all)[0]
    decena = (int(sum_first_digit) + 1) * 10
    validator = decena - sum_all
    if validator == 10:
        validator = 0

    return validator == int(uid[-1])


def validate_uid_and_ruc(uid):
    if len(uid) == 13:
        return validate_ruc(uid)
    if len(uid) == 10:
        return validate_cedula(uid)
    else:
        return False


def value_from_cents(cents):
    if not cents:
        return Decimal(0)
    return Decimal(cents) / 100


def get_total(items):
    return value_from_cents(sum((i.total for i in items)))
