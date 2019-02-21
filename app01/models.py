from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    '''用户模型类'''

    class Meta:
        db_table = 'fm_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
