import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'django_graphene.settings')

import django
django.setup()
from django.contrib.auth import get_user_model
from django_redis import get_redis_connection
from django.db import transaction
from articles.models import Article, Likes, Voter


def sync():
    con = get_redis_connection()

    # 同步用户点赞列表到mysql voter

    article_id_list = Article.objects.values_list('id', flat=True)
    for i in article_id_list:
        voter_of_redis = 'voter_of_{}'.format(i)
        voters = con.smembers(voter_of_redis)
        like = 0
        with transaction.atomic():
            for user_id in voters:
                Voter.objects.get_or_create(voted_by_id=user_id, article_id=i)
                like = like + 1
            # lookup by id_id, update into defaults
            Likes.objects.update_or_create(id_id=i, defaults={'num': like})


if __name__ == "__main__":
    print("start synchronizing...")
    sync()
    print("synchronization finished")


