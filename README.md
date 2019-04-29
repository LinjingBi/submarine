## 创建项目根目录django_graphene
```
mkdir django_graphene
```
## 创建虚拟环境lee
```
pip install virtualenv
pip install virtualenvwrapper
source virtualenvwrapper.sh
mkvirtualenv lee
workon lee
```
## 虚拟环境下，安装项目依赖
```
pip install -r <where_is_requirements.txt_>/requirements.txt
pip list
```
## 项目根目录下，创建django项目，创建app
```
django-admin startproject django_graphene
cd django_graphene
python manage.py startapp articles
```
## 修改项目settings.py配置
```
ALLOWED_HOST=['*']

INSTALLED_APPS = (
# .....
'graphene_django',
'articles',
)

GRAPHENE = {
   'SCHEMA': 'django_graphene.schema.schema',
}

# 添加token refresh中间件
MIDDLEWARE = [
# .....
    'middleware.jwtcontrol.RefreshTokenMiddleware',
]

# 设置mysql为数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': <database name>,
        'USER': <username>,
        'PASSWORD': <user password>,
        'HOST': <host>,
        'PORT': <connection port>,

    }
}

# 设置时区
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = False

# 配置graphene
GRAPHENE = {
    'SCHEMA': 'django_graphene.schema.schema',
    'MIDDLEWARE': [
        'middleware.RateThrottle.RateThrottleMiddleware',
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# 将graphql_jwt加入authentication backends
AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# django-graphql-jwt验证参数
GRAPHQL_JWT = {
    'JWT_AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=5),
}

# redis cache backend
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': XXXXX,
            'PICKLE_VERSION': -1,    # Use the latest protocol version
            'SOCKET_CONNECT_TIMEOUT': 5,  # in seconds
            'SOCKET_TIMEOUT': 5,  # in seconds
        }
    }
}

# 设置 RateThrottle
NUM_PROXIES = 0
# 1分钟最多访问30次
TIME_DELTA = 60  # in seconds
VISIT_TIMES = 30
# 设置访问频率限制graphql api
LIMIT_FIELD_NAME = {'GetAllTags', 'GetArticles', 'GetArticle'}

# 设置token失效 缓冲区
TOKEN_EXPIRE_DELAY = timedelta(seconds=60)
```
