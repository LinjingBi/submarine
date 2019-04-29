import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'django_graphene.settings')

import django
django.setup()
from django.contrib.auth import get_user_model
# from django_redis import get_redis_connection
from django.db import transaction
from articles.models import Article, TagList, Likes


def populate():
    with transaction.atomic():
        init_users = {"username": ["larva_001", "larva_002"],
                      "password": ["tudoutudouwoshifanqie", "fanqiefanqiewoshitudou"],
                      "email": ['1260935104@qq.com', 'bilinjing330@gmail.com']}
        init_articles = {'title': ['The Day We Were Born', 'I Love FRIED CHICKEN'],
                         'content': ['2019/04/29 17:10 Sunny', "McDonald's is my favorite"],
                         'posted_by': [1, 2]}
        init_tags = {'name': ['The Greatest', 'Bird Set Free', 'Alive', 'Unstoppable', 'Sia']}

        # create user
        user = get_user_model()
        for i in range(2):
            u = user.objects.create(username=init_users['username'][i], email=init_users["email"][i])
            u.set_password(init_users['password'][i])
            u.save()
        # publish article
        for i in range(2):
            a = Article.objects.create(title=init_articles['title'][i], content=init_articles['content'][i]
                                       , posted_by_id=init_articles['posted_by'][i])
            Likes.objects.create(id=a)

        # create tag list
        TagList.objects.bulk_create([TagList(name=init_tags['name'][i]) for i in range(2)])


if __name__ == "__main__":
    print('db start initializing...')
    populate()
    print('initialization finished')



