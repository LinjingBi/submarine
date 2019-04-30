import time
import pickle

import graphene
from graphene import resolve_only_args
from graphene_django import DjangoObjectType, DjangoConnectionField
from graphql_jwt.decorators import login_required
from django_redis import get_redis_connection
from django.db import IntegrityError, transaction

from .models import Article, Likes, TagList, ArticleTag
from .utils import test_article_id, test_id, test_article, get_like, test_tag


class ArticleType(DjangoObjectType):
    class Meta:
        model = Article
        interfaces = (graphene.relay.Node, )


class TagListType(DjangoObjectType):
    class Meta:
        model = TagList


class ArticleTagType(DjangoObjectType):
    class Meta:
        model = ArticleTag


class ArticleInfoType(graphene.ObjectType):
    body = graphene.Field(ArticleType)
    tags = graphene.List(TagListType)
    likes = graphene.Int()


class DraftList(graphene.ObjectType):
    id = graphene.String()
    title = graphene.String()
    content = graphene.String()


class AddTag(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        article_id = graphene.String(required=True)
        tag_id = graphene.String(required=True)

    @login_required
    def mutate(self, info, article_id, tag_id):
        user = info.context.user
        art_id = test_article_id(article_id)
        tg_id = test_id(tag_id)

        cn = get_redis_connection()
        article_redis = 'article_{}'.format(art_id)

        # 测试文章id是否存在
        group_object = test_article(cn, art_id)

        # 只有作者能给自己的文章加tag
        if group_object[0].posted_by.id != user.id:
            raise Exception('Only the poster can add tag')

        # 测试tag id是否有效
        tag_object = test_tag(cn, tg_id)

        # 一篇文章只能有一个tag
        if tag_object in group_object[1]:
            raise Exception('Tag has been added')

        # article_id, tag_id全都合格后，先删掉缓存，然后修改mysql，再同步到redis
        cn.delete(article_redis)
        try:
            # 更新articletag表的同时也要更新article表里的更新时间
            # 两句sql必须保证原子性，就用了事务
            with transaction.atomic():
                # tag_name=='NO TAG'，是一个无tag的tag，如果添加这个，以前的tag都要删除
                if tag_object.name != 'NO TAG':
                    ArticleTag.objects.create(article_id=art_id, tag_id=tg_id)
                    pair = ArticleTag.objects.select_related('tag').filter(article_id=art_id)
                    group_object[1] = {item.tag for item in pair}
                else:
                    ArticleTag.objects.filter(article_id=art_id).delete()
                    group_object[1] = set()
                # save 自动更新 文章的修改时间
                group_object[0].save()
                cn.set(article_redis, pickle.dumps(group_object))
                cn.expire(article_redis, 60 * 30)

                ok = True
                return AddTag(ok=ok)
        except IntegrityError:
            # 已经进行过一次重复添加测试，如果还是出现integrity error，说明mysql写入新数据，要重新读取
            new_tags = ArticleTag.objects.select_related('tag').filter(article_id=art_id)
            group_object[1] = {item.tag for item in new_tags}
            cn.set(article_redis, pickle.dumps(group_object))
            cn.expire(article_redis, 60 * 30)
            raise Exception('Tag has been added')


class LikeArticle(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        article_id = graphene.String(required=True)

    @login_required
    def mutate(self, info, article_id):
        """
        点赞行为先存在redis，再通过第三方同步到mysql，因为点赞是很频繁的写操作
        :param info:
        :param article_id:
        :return:
        """
        # redis里面点赞排行榜是zset，名字是article_like score like member article_id
        # 同时需要一个某文章点赞用户的set，来实现一篇文章只能被一个用户点赞一次
        # set key vote_of_{article_id} member user_id

        user = info.context.user
        int_id = test_article_id(article_id)

        con = get_redis_connection()
        # 先测试文章是否存在
        test_article(con, int_id)

        # 去重测试
        voter_of_redis = 'voter_of_{}'.format(int_id)
        if con.sadd(voter_of_redis, user.id):
            get_like(con, int_id, vote=True)
            ok = True
            return LikeArticle(ok=ok)

        raise Exception('one article one chance to like')


class CreateArticle(graphene.Mutation):
    new_article = graphene.Field(ArticleType)
    ok = graphene.Boolean()

    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        create_draft = graphene.Boolean()
        draft_id = graphene.String()

    @login_required
    def mutate(self, info, title, content, create_draft=False, draft_id=None):
        if create_draft and draft_id:
            raise Exception('do not create and publish draft in one request')
        writer = info.context.user

        if not create_draft:
            # 如果是发布草稿，就要先删掉redis里的备份
            con = get_redis_connection()
            if draft_id is not None:
                draft_redis = 'draft_box_{}'.format(writer.id)
                done = con.zremrangebyscore(draft_redis, float(draft_id), float(draft_id))
                if not done:
                    raise Exception('invalid draft id')
            try:
                with transaction.atomic():
                    atc = Article(posted_by=writer, title=title, content=content)
                    atc.save()
                    Likes.objects.create(id=atc)
                    article_redis = 'article_{}'.format(atc.id)
                    con.set(article_redis, pickle.dumps([atc, set()]))
                    con.expire(article_redis, 60*20)
                    return CreateArticle(new_article=atc, ok=True)
            except IntegrityError:
                raise Exception('article already exists')

        else:
            # 创建草稿箱
            con = get_redis_connection()
            # 一个用户一个草稿箱
            draft_redis = 'draft_box_{}'.format(writer.id)
            new_id = time.mktime(time.gmtime(time.time()))
            draft = [content, title]
            # {value: score}
            con.zadd(draft_redis, {pickle.dumps(draft): new_id})
            return CreateArticle(ok=True)


class Query(graphene.ObjectType):

    Get_all_tags = graphene.List(TagListType)
    Get_article = graphene.Field(ArticleInfoType, article_id=graphene.String())
    node = graphene.relay.Node.Field()
    Get_articles = DjangoConnectionField(ArticleType, description='All the articles')
    Get_drafts = graphene.List(DraftList)

    @login_required
    def resolve_Get_drafts(self, info):
        con = get_redis_connection()
        draft_redis = 'draft_box_{}'.format(info.context.user.id)
        draft_list = con.zrevrange(draft_redis, 0, -1, withscores=True)
        result = []
        for item, score in draft_list:
            pair = pickle.loads(item)
            result.append(DraftList(id=score, title=pair[1], content=pair[0]))
        return result

    @login_required
    def resolve_Get_article(self, info, article_id):
        con = get_redis_connection()
        int_id = test_article_id(article_id)

        group_object = test_article(con, int_id)
        score = get_like(con, int_id)
        return ArticleInfoType(body=group_object[0], tags=group_object[1], likes=score)

    @login_required
    @resolve_only_args
    def resolve_Get_articles(self, **kwargues):
        # article_like 文章的点赞sorted set
        # score like member article_id
        con = get_redis_connection()
        if not con.zcard('article_like'):
            ranking_list = Likes.objects.select_related().order_by('num')
            score_member = {}
            for i in range(min(len(ranking_list), 100)):
                score_member[ranking_list[i].id.id] = ranking_list[i].num if ranking_list[i].num else 0
                article_id = ranking_list[i].id.id
                article_redis = '{}_{}'.format('article', article_id)
                article = Article.objects.select_related('posted_by').get(id=article_id)
                article_tags_object = article.tag_list.select_related('tag').all()
                tags_object = {obj.tag for obj in article_tags_object}
                group_object = [article, tags_object]
                con.set(article_redis, pickle.dumps(group_object))
            con.zadd('article_like', score_member)
            con.expire('article_like', 60*60*24)

        article_list = con.zrevrange('article_like', 0, -1, withscores=True)
        result = []
        for i, score in article_list:
            result.append(test_article(con, i)[0])
        return result

    @login_required
    def resolve_Get_all_tags(self, info):
        """
        TagList本来存在mysql中，由于读取文章是在redis中进行，而文章大表没有tag这一栏
        所以需要redis里有ArticleTag来存放文章的tag，当我们给文章添加tag时，肯定会修改redis里的articlelist
        又因为添加tag，输入的是tag_id，所以如果redis中有tag列表，就可以在O（1）的时间里找到tag对象，而不是花logn去mysql找
        :param info:
        :return:
        """
        # tag_list在redis里是哈希 key tag_list
        # field1 tag_id1 value1 pickle.dumps(tag_object1) ....
        cn = get_redis_connection()
        tag_list_redis = cn.hvals('tag_list')
        if tag_list_redis:
            return [pickle.loads(tag) for tag in tag_list_redis]
        tag_list_mysql = TagList.objects.all()

        cn.hmset('tag_list', {tag.id: pickle.dumps(tag)for tag in tag_list_mysql})

        return tag_list_mysql


class Mutation(graphene.ObjectType):
    Create_article = CreateArticle.Field()
    Up_vote = LikeArticle.Field()
    Add_tag = AddTag.Field()
