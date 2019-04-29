from django.db import models
from django.conf import settings

# Create your models here.


class Article(models.Model):
    title = models.CharField(max_length=128)
    content = models.TextField()
    # likes = models.IntegerField(default=0)
    # auto_now_add 记录 create的时间，只在第一次创建
    create_date = models.DateTimeField(auto_now_add=True)
    # create_date = models.CharField(max_length=128)
    # auto_now 记录最后一次update，然后执行save时的时间，每次修改都会更新
    last_modified = models.DateTimeField(auto_now=True)
    # last_modified = models.CharField(max_length=128)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    # tags = models.CharField(max_length=128, default='')

    class Meta:
        # 一个用户不能发重名的文章
        unique_together = ('posted_by', 'title')


class Voter(models.Model):
    voted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)

    class Meta:
        # 一个用户只能点赞一篇文章一次
        unique_together = ('voted_by', 'article')


class Likes(models.Model):
    id = models.OneToOneField(Article, primary_key=True, on_delete=models.CASCADE)
    num = models.IntegerField(default=0)


class TagList(models.Model):
    name = models.CharField(max_length=56, null=False, unique=True)


class ArticleTag(models.Model):
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='tag_list')
    tag = models.ForeignKey('articles.TagList', on_delete=models.CASCADE, related_name='article_list')

    class Meta:
        # 一篇文章一种tag只能加一次
        unique_together = ('article', 'tag')

#
# class Draft(models.Model):
#     title = models.CharField(max_length=128, null=True)
#     content = models.TextField(null=True)
#     create_date = models.DateTimeField(auto_now_add=True)
#     posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
