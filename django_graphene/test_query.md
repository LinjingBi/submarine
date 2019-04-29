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
请将注册返回的token，或Insomnia返回的响应header中set-cookie一栏，或cookie中，复制出token，并新建/添加在请求头部的Authorization一栏，如下所示
```
Authorization    JWT <token>   // 以JWT开头，空格隔开
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
请将返回的token，或Insomnia返回的响应header中set-cookie一栏，或cookie中，复制出token，并新建/添加在请求头部的Authorization一栏。
## 退出登陆 LogOut
退出登录后，仍旧使用以前的token发送请求，将会收到401 zombie...。
```
mutation logout{
  LogOut{
    ok
  }
}
```
**以下的接口测试全部需要登陆验证，请确保正确设置Authorization。以下的接口每次访问都会将refresh token放置在响应的set-cookie中（以jwt=开头），请及时更新请求头部的token。**
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





