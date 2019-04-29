import time
import datetime
import jwt

from django.conf import settings as django_settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django_redis import get_redis_connection

from graphql_jwt.utils import get_user_by_payload
from graphql_jwt.settings import jwt_settings
from graphql_jwt import exceptions


class RefreshTokenMiddleware(MiddlewareMixin):
    """根据设置的token过期缓冲区，刷新token，以应对高并发环境下的用户请求"""

    def decode(self, token, verify, options, context=None):
        payload = jwt.decode(
            token,
            jwt_settings.JWT_SECRET_KEY,
            verify,
            options=options,
            leeway=jwt_settings.JWT_LEEWAY,
            audience=jwt_settings.JWT_AUDIENCE,
            issuer=jwt_settings.JWT_ISSUER,
            algorithms=[jwt_settings.JWT_ALGORITHM])
        return payload

    def get_payload(self, token, verify=False, options=None, context=None):
        try:
            payload = self.decode(token, verify, options, context)
        except jwt.ExpiredSignature:
            raise exceptions.JSONWebTokenExpired()
        except jwt.DecodeError:
            raise exceptions.JSONWebTokenError(_('Error decoding signature'))
        except jwt.InvalidTokenError:
            raise exceptions.JSONWebTokenError(_('Invalid token'))
        return payload

    def refresh_token(self, token, user, context=None):
        payload = self.get_payload(token, True, options={
            'verify_exp': jwt_settings.JWT_VERIFY_EXPIRATION,
            }, context=context)
        orig_iat = payload.get('origIat')

        if not orig_iat:
            raise exceptions.JSONWebTokenError(_('origIat field is required'))

        if jwt_settings.JWT_REFRESH_EXPIRED_HANDLER(orig_iat, context):
            raise exceptions.JSONWebTokenError(_('Refresh has expired'))

        payload = jwt_settings.JWT_PAYLOAD_HANDLER(user, context)
        payload['origIat'] = orig_iat
        refresh_token = jwt_settings.JWT_ENCODE_HANDLER(payload, context)

        return payload, refresh_token

    def process_request(self, request):
        jwt_header = django_settings.GRAPHQL_JWT['JWT_AUTH_HEADER_NAME']
        temp = request.META.get(jwt_header, '').split()
        token = temp[1] if len(temp) == 2 and temp[0] == jwt_settings.JWT_AUTH_HEADER_PREFIX else None
        if token:
            payload = self.get_payload(token)
            exp = payload['exp']

            # 都用utc/gm时间 utc只是精度比gm高，时区都是一样的
            exp_datetime = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(exp)))
            now = datetime.datetime.utcnow()

            # name: token_userid key:token score:exp
            user = get_user_by_payload(payload)
            token_set = "token_{}".format(user.id)
            con = get_redis_connection()
            rank = con.zrank(token_set, token)

            # 由于登陆/注册领到的第一个token，在当时并不会存进redis，此时token_set就是空的
            if rank is None:
                # 用登陆后的第一个token来发起第一次请求，但是token已经过期
                if now > exp_datetime:
                    return
                # 检查是否是已经登出的token
                zombie_set = "zombie_{}".format(user.id)
                zombie = con.zrank(zombie_set, token)
                if zombie is not None:
                    return JsonResponse({'message': 'zombie..'}, status=401)
                # 初次登陆的用户
                con.zadd(token_set, {token: exp})
                alive = django_settings.GRAPHQL_JWT['JWT_EXPIRATION_DELTA'] + django_settings.TOKEN_EXPIRE_DELAY
                con.expire(token_set, alive)
                setattr(request, 'jwt', token)

            else:
                # token超过了过期缓冲期，清除包括它的之前的所有token
                if now - exp_datetime > django_settings.TOKEN_EXPIRE_DELAY:
                    con.zremrangebyrank(token_set, 0, rank)
                else:
                    latest = con.zrange(token_set, -1, -1)[0]
                    if latest:
                        try:
                            payload, refresh_token = self.refresh_token(latest, user)
                            new_exp = payload['exp']
                            con.zadd(token_set, {refresh_token: new_exp})
                            alive = django_settings.GRAPHQL_JWT['JWT_EXPIRATION_DELTA'] + django_settings.TOKEN_EXPIRE_DELAY
                            con.expire(token_set, alive)
                            new_token = '{} {}'.format(temp[1], refresh_token)
                            request.META[jwt_header] = new_token
                            setattr(request, 'jwt', refresh_token)
                        # 如果最新的token也过期了，删token缓存，再交给后面的graphql_jwt中间件返回错误
                        except exceptions.JSONWebTokenError:
                            con.zremrangebyrank(token_set, 0, -1)



