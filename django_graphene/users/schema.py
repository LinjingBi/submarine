import datetime
import time

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import AnonymousUser

import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphql_jwt.utils import get_payload
from django_redis import get_redis_connection
from redis import exceptions


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class CreateUser(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = get_user_model()(username=username, email=email)
        user.set_password(password)
        user.save()
        ok = True
        return CreateUser(ok=ok)


class Logout(graphene.Mutation):
    ok = graphene.Boolean()

    @login_required
    def mutate(self, info):
        token = getattr(info.context, 'jwt')
        payload = get_payload(token)
        # 方便删除set-cookie中的jwt
        setattr(info.context, 'logout', True)

        used = 'token_{}'.format(info.context.user.id)
        zombie = 'zombie_{}'.format(info.context.user.id)
        info.context.user = AnonymousUser()
        con = get_redis_connection()
        try:
            con.rename(used, zombie)
            exp_datetime = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(payload['exp'])))
            now_datetime = datetime.datetime.utcnow()
            dod = (exp_datetime-now_datetime).total_seconds()
            con.expire(zombie, dod)
            # logout(info.context)
        except exceptions.ResponseError:
            pass
        return Logout(ok=True)


class Query(graphene.ObjectType):
    User_profile = graphene.List(UserType)

    @login_required
    def resolve_users(self, info, **kwargs):
        return get_user_model().objects.get(id=info.context.user.id)


class Mutation(graphene.ObjectType):
    Create_user = CreateUser.Field()
    Log_in = graphql_jwt.ObtainJSONWebToken.Field()
    Log_out = Logout.Field()
