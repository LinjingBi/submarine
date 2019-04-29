## 安装Insomnia
- [下载链接](https://insomnia.rest/)
- [使用教程](https://support.insomnia.rest/article/61-graphql)  
安装完毕后，使用Insomnia生成graphql请求，进行接口测试。
## 用户注册
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
## 用户登陆
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
## 退出登陆
```
mutation logout{
  LogOut{
    ok
  }
}
```
**以下的接口测试全部需要登陆验证，请确保正确设置Authorization。以下的接口每次访问都会将refresh token放置在响应的set-cookie中（以jwt=开头），请及时更新请求头部的token。**
## 



