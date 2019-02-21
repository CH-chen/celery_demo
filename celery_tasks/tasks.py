from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time

#django环境初始化
#下面四句加到任务处理者一段，即ubuntu里面的任务处理者，ubuntu作为处理者，要把全部代码复制过去
#ubuntu中启动命令 celery -A celery_tasks.tasks worker -l info
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "celery_demo.settings")
django.setup()

# 创建一个celery的实例对象
app = Celery("celery_tasks.tasks",broker='redis://:chenchen@192.168.170.141:6379/8')

#定义任务函数
@app.task
def send_register_active_email(to_email,username,token):
    #发送激活邮件
    subject = "天猫商城欢迎你"
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = "<h1>%s欢迎成为会员</h1>请点击以下链接激活账户</br><a href='http://127.0.0.1:8000/active/%s'>http://127.0.0.1:8000/active/%s</a>" % (
    username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(3)
