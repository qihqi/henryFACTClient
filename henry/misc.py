''' Miscellanous stuff'''

import re

def id_type(uid):
    if uid == 'NA' or uid.startswith('9999'):
        return '07'  # General

    uid = fix_id(uid)
    if len(uid) == 10:
        return '05'  # cedula
    elif len(uid) == 13:
        return '04'  # RUC
    else:
        print 'error!! uid {} with length {}'.format(uid, len(uid))
    return '07'

def fix_id(uid):
    uid = fix_id_error(uid)
    if uid == 'NA':
        return '9' * 13 # si es consumidor final retorna 13 digitos de 9
    uid = re.sub('[^\d]', '', uid)
    if not validate_uid_and_ruc(uid):
        return '9' * 13
    return uid

def abs_string(string):
    if string.startswith('-'):
        return string[1:]
    return string


def validate_uid_and_ruc(uid):
    if len(uid) == 13:
        uid = uid[:10]
    if len(uid) != 10:
        return False
    first_digits = int(uid[:2])
    if first_digits < 1 or first_digits > 24:
        return False

    sum_even = 0
    sum_old = 0
    for i, x in enumerate(uid):
        d = int(x)
        if i % 2 == 1: # it is 0 indexed, so odd positions have even index
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

