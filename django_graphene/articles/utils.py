import pickle
from graphql_relay import from_global_id
from django.core.exceptions import ObjectDoesNotExist
from .models import Article, Likes, TagList, ArticleTag


def test_article_id(str_id):
    _, int_id = from_global_id(str_id)
    return int_id


def test_id(str_id):
    try:
        temp = int(str_id)
    except ValueError:
        raise Exception('id should be an integer')
    if temp <= 0:
        raise Exception('id should be a positive integer')
    return temp


def test_article(cn, article_id):
    # article在redis中的储存形式是字符串对象， key article（固定字节）_id（文章id） value pickle([article object, taglist object])
    article_redis = '{}_{}'.format('article', article_id)
    article_re = cn.get(article_redis)
    if article_re:
        group_object = pickle.loads(article_re)
    else:
        # 如果redis没有，先设置一个空的article键，防止连续的恶意攻击，
        # 然后再去mysql
        temp_article = 'temp_atcl_{}'.format(article_id)
        if cn.get(temp_article):
            raise Exception('article does not exist')
        # 先设置空键，再去mysql查找，防止密集攻击的缓存击穿，穿透
        cn.set(temp_article, 1, ex=180)
        try:
            article = Article.objects.select_related().get(id=article_id)
            article_tags_object = article.tag_list.select_related('tag').all()
            tags_object = {obj.tag for obj in article_tags_object}
            group_object = [article, tags_object]
            cn.set(article_redis, pickle.dumps(group_object))

        except ObjectDoesNotExist:
            raise Exception('article does not exist')
    return group_object


def get_like(con, int_id, vote=False):
    # use after test_article() to make sure int_id is valid
    article_like_redis = 'article_like'
    val = con.zscore(article_like_redis, int_id)
    if isinstance(val, float):
        incr = 1
    else:
        try:
            cur = Likes.objects.get(id=int_id)
            val = cur.num
            incr = val + 1
        except ObjectDoesNotExist:
            raise Exception('article does not exist')
    if vote:
        # zincrby(name, amount, member)
        con.zincrby(article_like_redis, incr, int_id)

    return val


def test_tag(cn, tg_id):
    # tag_list在redis里是哈希 key tag_list
    # field1 tag_id1 value1 pickle.dumps(tag_object1) field 2 ....
    tag_list_name = 'tag_list'
    tag_re = cn.hget(tag_list_name, tg_id)
    if tag_re:
        tag_object = pickle.loads(tag_re)
    else:
        # 正确的tagid都存在hash表里，不正确的设置临时字符串 key temp_tag_id value 1
        temp_tag = 'temp_tag_{}'.format(tg_id)
        if cn.get(temp_tag):
            raise Exception('tag does not exist')
        else:
            cn.set(temp_tag, 1, ex=30)
            try:
                tag_object = TagList.objects.get(id=tg_id)
                # 向hash里添加一个tag
                cn.hset(tag_list_name, tg_id, pickle.dumps(tag_object))

            except ObjectDoesNotExist:
                raise Exception('tag does not exist')
    return tag_object




