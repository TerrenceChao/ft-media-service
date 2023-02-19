

def res_success(data=None, msg="ok", code="0"):
    return {
        "code": code,
        "msg": msg,
        "data": data,
    }


def res_err(data=None, msg="error", code="1"):
    return {
        "code": code,
        "msg": msg,
        "data": data,
    }
