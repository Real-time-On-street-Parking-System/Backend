from flask import request
from jose import JWTError, jwt


class Auth:
    TOKEN = str(open('docs/token').read())
    SECRET = str(open('docs/secret').read())

    @classmethod
    def crate_access_token(cls, data={}) -> str:
        """
        根據 data 產生 jwt token
        :params data (dict): 要加密的內容
        """

        to_encode_data = data.copy()
        to_encode_data.update({
            'secret': cls.SECRET
        })
        encoded_jwt_token = jwt.encode(
            to_encode_data, cls.TOKEN, algorithm='HS256')

        return encoded_jwt_token

    @classmethod
    def verify_token(cls, api) -> None:
        """
        驗證 access token 是否合法
        :params request: Flask request
        """

        def decorator():
            try:
                # 取得放在 request header 裡的 token
                headers = request.headers
                access_token = headers.get(
                    'Authorization').replace('Bearer ', '')
                payload = jwt.decode(
                    access_token, cls.TOKEN, algorithms=['HS256'])
                if payload.get('secret') != cls.SECRET:
                    raise JWTError
            except:
                raise JWTError

            api()

        return decorator
