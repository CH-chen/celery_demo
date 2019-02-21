from django.shortcuts import render,redirect,HttpResponse

from django.core.urlresolvers import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from celery_tasks.tasks import send_register_active_email
from app01.models import User
from django.contrib.auth import authenticate,login,logout

import re
# Create your views here.

##########注册第一种FBV模式#########
#注册和注册处理合一起
def register1(request):
    if request.method == "GET":
        return render(request,'register.html')
    else:
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        re_password = request.POST.get("cpwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")

        if not all([username, password, re_password, email]):
            return render(request, 'register.html', {"errmsg": '数据不完整'})
        # 第一种校验用户名
        # name_exist= models.User.objects.filter(username=username)
        # if name_exist:
        #     return render(request, 'register.html', {"error": '用户名已存在'})
        # 第二种校验用户名
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            return render(request, 'register.html', {"errmsg": '用户名已存在'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {"error": '邮箱格式不正确'})
        if allow != "on":
            return render(request, 'register.html', {"errmsg": '请同意协议'})

        user = User.objects.create_user(username=username, password=password, email=email)
        # django内置的user中有一个is_active,注册成功默认激活，这里不认他激活
        user.is_active = 0
        user.save()


        return redirect(reverse('goods:index'))

#注册和注册处理分开写
# def register_handle(request):
#     username = request.POST.get("user_name")
#     password = request.POST.get("pwd")
#     re_password = request.POST.get("cpwd")
#     email = request.POST.get("email")
#     allow = request.POST.get("allow")
#
#     if  not all([username,password,re_password,email]):
#         return render(request,'register.html',{"error":'数据不完整'})
#     #第一种校验用户名
#     # name_exist= models.User.objects.filter(username=username)
#     # if name_exist:
#     #     return render(request, 'register.html', {"error": '用户名已存在'})
#     #第二种校验用户名
#     try:
#         user = models.User.objects.get(username=username)
#     except models.User.DoesNotExist:
#         #用户名不存在
#         user=None
#     if user:
#         return render(request, 'register.html', {"error": '用户名已存在'})
#
#     if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
#         return render(request, 'register.html', {"error": '邮箱格式不正确'})
#     if allow != "on" :
#         return render(request, 'register.html', {"error": '请同意协议'})
#
#     user = models.User.objects.create_user(username=username,password=password,email=email)
#     #django内置的user中有一个is_active,注册成功默认激活，这里不认他激活
#     user.is_active = 0
#     user.save()
#     return redirect(reverse('goods:index'))

##########注册第二种CBV模式#####

class RegisterView(View):
    def get(self,request):
        return render(request, 'register.html')

    def post(self,request):
        print("=========")
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        re_password = request.POST.get("cpwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")
        print(username,password,re_password,email)

        if not all([username, password, re_password, email]):
            return render(request, 'register.html', {"errmsg": '数据不完整'})
        # 第一种校验用户名
        # name_exist= models.User.objects.filter(username=username)
        # if name_exist:
        #     return render(request, 'register.html', {"error": '用户名已存在'})
        # 第二种校验用户名
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            return render(request, 'register.html', {"errmsg": '用户名已存在'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {"errmsg": '邮箱格式不正确'})
        if allow != "on":
            return render(request, 'register.html', {"errmsg": '请同意协议'})

        user = User.objects.create_user(username=username, password=password, email=email)
        # django内置的user中有一个is_active,注册成功默认激活，这里不认他激活
        user.is_active = 0
        user.save()

        #发送激活邮件，激活连接地址http://127.0.0.1:8000/user/active/2
        #激活连接中要有用户的身份信息，为了防止恶意激活，要对用户信息加密
        #加密用户信息，生成激活token
        serialize = Serializer(settings.SECRET_KEY,3600)
        info = {"confirm":user.id}
        token = serialize.dumps(info) #byte类型
        token = token.decode() #转成utf8

        #发送邮件
        send_register_active_email.delay(email,username,token)


        return redirect('/index')

#激活视图
class ActiveView(View):
    def get(self,request,token):
        serialize = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serialize.loads(token)   #解密
            #获取待激活的用户id
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            #激活成功，返回登录页面
            return redirect('/login')

        except SignatureExpired as e:
            return HttpResponse("激活链接已过期")

class LoginView(View):
    def get(self,request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get("username")
            checked = 'checked' #勾选记住用户名
        else:
            username = ''
            checked = ''
        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        #登录校验
        username = request.POST.get("username")
        password = request.POST.get("pwd")

        if not all([username,password]):
            return render(request,'login.html',{'errmsg':"数据不完整"})

        user = authenticate(username=username,password=password)
        if user is not None:
            #判断用户是否激活
            if user.is_active:
                login(request, user)  #login()使用Django的session框架来将用户的ID保存在session中
                #默认跳转到主页,即如果用户直接在login登录则默认跳转主页，如果其他页面转到，则跳转之前页面
                next_url = request.GET.get("next",reverse('index'))
                response = redirect(next_url)#跳转到首页
                remember = request.POST.get("remember")
                if remember == "on":
                    #记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg': "用户未激活"})
        else:
            return render(request, 'login.html', {'errmsg': "用户名或密码错误"})

# /user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出登录'''
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('index'))


class IndexView(View):
    def get(self, request):
        '''退出登录'''
        # 清除用户的session信息


        # 跳转到首页
        return render(request,'index.html')
