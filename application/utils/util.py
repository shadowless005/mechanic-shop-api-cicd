from application.extensions import db
from application.models import Customer

from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, jsonify, current_app, g
from jose import jwt
import jose


def encode_token(customer_id):
    payload = {
    
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "sub": str(customer_id)
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]

            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    raise ValueError("Expected Bearer authorization")
            except ValueError:
                return jsonify({
                    "message": "Invalid authorization header."
                }), 401

        if not token:
            return jsonify({
                "message": "Token is missing!"
            }), 401

        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )

            customer_id = int(data["sub"])

        except jose.exceptions.ExpiredSignatureError:
            return jsonify({
                "message": "Token has expired!"
            }), 401

        except (jose.exceptions.JWTError, KeyError, ValueError, TypeError):
            return jsonify({
                "message": "Invalid token!"
            }), 401

        customer = db.session.get(Customer, customer_id)
        if customer is None:
            return jsonify({"message": "Authenticated customer no longer exists."}), 401
        g.current_customer = customer

        return f(customer_id, *args, **kwargs)

    return decorated

def staff_required(f):
    @wraps(f)
    @token_required
    def decorated(customer_id, *args, **kwargs):
        customer = db.session.get(Customer, int(customer_id))

        if customer is None:
            return jsonify({
                "message": "Authenticated customer no longer exists."
            }), 401

        if not customer.is_staff:
            return jsonify({
                "message": "Staff access required."
            }), 403

        return f(*args, **kwargs)

    return decorated