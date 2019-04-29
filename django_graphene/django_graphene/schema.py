import graphene
import graphql_jwt
import articles.schema
import users.schema


class Query(users.schema.Query, articles.schema.Query, graphene.ObjectType):
    pass


class Mutation(users.schema.Mutation, articles.schema.Mutation, graphene.ObjectType):
    # verify_token = graphql_jwt.Verify.Field()
    # refresh_token = graphql_jwt.Refresh.Field()
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)

