from bottle import abort


def get_property_or_fail(request, name, failstatus=400, failmessage=''):
    result = request.get(name, None)
    if result is None:
        abort(failstatus, failmessage)
    return result
