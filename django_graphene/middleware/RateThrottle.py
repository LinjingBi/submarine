from django.utils.deprecation import MiddlewareMixin
from django.conf import settings as django_settings
from django.core.cache import cache
from graphql import GraphQLError
import datetime
import jwt
from django_redis import get_redis_connection
from graphql_jwt.utils import get_user_by_payload
from graphql_jwt.settings import jwt_settings
from graphql_jwt import exceptions


class RateThrottleMiddleware(object):
    """
     根据request.META['HTTP_X_FORWARDED_FOR'] 或者
     request.META['REMOTE_ADDR']在redis中，建立有过期时间的键
     前者是用户真实ip
     后者有可能有proxy，就会是最后一个proxy的ip，不能被伪造，
     因为这个是跟服务端建立tcp联系的服务器
     参考：https://www.jianshu.com/p/15f3498a7fad
     """

    def resolve(self, next, root, info, **args):
        field = info.field_name
        if field in django_settings.LIMIT_FIELD_NAME:
            time_delta = django_settings.TIME_DELTA
            visit_times = django_settings.VISIT_TIMES

            def get_ip(request):
                xff = request.META.get('HTTP_X_FORWARDED_FOR', None)
                remote_addr = request.META.get('REMOTE_ADDR', None)
                # 指的是从最后一个代理开始数，第几个ip是我们要的
                num_proxies = django_settings.NUM_PROXIES

                if num_proxies:
                    if num_proxies == 0 or xff is None:
                        return remote
                    else:
                        proxies = xff.split(',')
                        client_addr = proxies[-min(num_proxies, len(proxies))]
                        return client_addr.strip()
                return ''.join(xff.split()) if xff else remote_addr

            addr = get_ip(info.context)

            target = '{}{}'.format(addr, field)
            visits = cache.get(target)
            if visits and visits == visit_times:
                return GraphQLError('Take a break...')
            elif visits:
                cache.incr(key=target, ignore_key_check=True)
            else:
                cache.incr(key=target, ignore_key_check=True)
                cache.expire(target, timeout=time_delta)
        return next(root, info, **args)


















