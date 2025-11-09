from flask import redirect, request
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError

def jwt_noapi_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except NoAuthorizationError:
            return redirect('/login')
        except Exception:
            return redirect('/login')

        return f(*args, **kwargs)

    return decorated
