## 采用[django-graphql-jwt](https://django-graphql-jwt.domake.io/en/stable/quickstart.html)进行身份验证
因为使用[jwt_cookie](https://django-graphql-jwt.domake.io/en/stable/authentication.html#per-cookie)将token存在响应头部的set-cookie中，
所以可以直接使用GraphiQL进行调试。
## 使用GraphiQL进行接口测试
执行了python manage.py runserver语句后，在浏览器输入url
```
http://<web_server_ip>:<port_id>/graphql/
```
进入GraphQL界面，输入相关query进行测试。
## 用户注册 CreateUser
```
mutation register($username:String!, $password:String!, $email:String!){
  CreateUser(username:$username, password:$password, email:$email){
    ok
  }
  LogIn(username:$username, password:$password){
    token
  }
}

// query variables

{"username": xxxx,
  "password": xxxx,
  "email": xxxx
}
```
## 用户登陆 LogIn
使用[init_db.py](https://github.com/LinjingBi/submarine/blob/master/django_graphene/init_db.py)预设的用户，或自行注册的用户登陆。
```
mutation login($username:String!, $password:String!){
  LogIn(username:$username, password:$password){
    token
  }
}

// query variables

{"username": xxxx,
  "password": xxxx,
}
```
## 退出登陆 LogOut
退出登录后，仍旧使用以前的token发送请求，将会收到401 zombie...。
```
mutation logout{
  LogOut{
    ok
  }
}
```
## 获取文章列表（按照点赞次数排序，relay风格） GetArticles
**建议保存id，方便后面接口使用**
```
query{
  GetArticles(first: xx, last: xx, after: xx, before: xx){
    edges{
      node{
        id,
        title,
        content,
        postedBy{
          username
        },
        createDate,
        lastModified
      }
    }
    pageInfo{
      startCursor,
      endCursor,
      hasNextPage,
      hasPreviousPage
    }
  }
}
```
## 获取全部tag GetAllTags
**建议保存id，方便后面接口使用**
```
query{
GetAllTags{
  id,
  name
}
}

```
## 为文章添加tag AddTag
**注意**
- 默认一个文章可以有多个tag
- 只有文章的作者可以给文章添加tag
- 同一个tag一篇文章只能添加一次
- 如果添加叫NO TAG的标签，之前的标签（如果有）全部删除
```
mutation add($articleId:String!, $tagId:String!){
  AddTag(articleId: $articleId, tagId: $tagId){
    ok
  }
}

// query variables

{
  "articleId": <id_from_GetArticles>,
  "tagId": <id_from_GetAllTags>
}

```
## 获取单个文章详情 GetArticle
```
query get($articleId:String!){
  GetArticle(articleId:$articleId){
    body{
      id,
      title,
      content,
      lastModified,
      createDate,
      postedBy{
        username
      }
    }
    tags{
      name
    }
    likes
  } 
}

// query variables
{
  "articleId": <id_from_GetArticles>
}
```
## 点赞 UpVote
**注意**
- 一篇文章一个用户只能点赞一次，不可取消
```
mutation vote($articleId:String!){
  UpVote(articleId:$articleId){
    ok
  }
}

// query variables

{
  "articleId": <id_from_GetArticles>
}
```
## 创建文章/保存草稿/发布草稿成为文章 CreateArticle
**入参说明**
- create_draft：boolean，为True表示该文章要保存到草稿箱，默认为False。
- draft_id：String，草稿id，来自GetDrafts接口，默认为None。
- title：String，文章标题
- content：String， 文章内容
### 创建文章模式
```
mutation create($title:String!, $content:String!){
  CreateArticle(title:$title, content:$content){
    newArticle{
      title,
      content,
      createDate,
      lastModified,
      postedBy{
        username
      }
    }
  }
}

// query variables

{
  "title": "XXXXX",
  "content": "XXXXXXXXXXXX"
}
```
### 保存草稿模式
```
mutation create($title:String!, $content:String!){
  CreateArticle(title:$title, content:$content, createDraft: true){
    ok
  }
}

// query variables

{
  "title": "XXXXX",
  "content": "XXXXXXXXXXXX"
}
```
### 发布草稿模式
```
mutation create($title:String!, $content:String!, $draftId:String!){
  CreateArticle(title:$title, content:$content, createDraft: true, draftId: $draftId){
    ok
  }
}

// query variables

{
  "title": "XXXXX",
  "content": "XXXXXXXXXXXX",
  "draftId": <id_from_GetDrafts>,
}
```
## 获取草稿箱列表 GetDrafts
```
query{
  GetDrafts{
    id,
    title,
    content
  }
}
```




