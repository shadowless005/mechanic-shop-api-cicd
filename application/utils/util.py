from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, jsonify
from jose import jwt
import jose

SECRET_KEY = "mechanic-shop-secret-key"

def encode_token(customer_id):
    payload = {
    
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "sub": str(customer_id)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]

            try:
                token = auth_header.split(" ")[1]
            except IndexError:
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
                SECRET_KEY,
                algorithms=["HS256"]
            )

            customer_id = data["sub"]

        except jose.exceptions.ExpiredSignatureError:
            return jsonify({
                "message": "Token has expired!"
            }), 401

        except jose.exceptions.JWTError:
            return jsonify({
                "message": "Invalid token!"
            }), 401

        return f(customer_id, *args, **kwargs)

    return decorated