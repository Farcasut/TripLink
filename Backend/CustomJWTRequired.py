from flask import redirect, request, current_app
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError, CSRFError

def jwt_noapi_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except NoAuthorizationError:
            return redirect('/login')
        except Exception as e:
            if current_app.debug:
                print(f'jwt_noapi_required: {e}')
                
            return redirect('/login')

        return f(*args, **kwargs)

    return decorated
