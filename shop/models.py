from django.db import models
from django.contrib.auth.models import AbstractUser


class WechatUser(AbstractUser):
    """微信小程序用户模型"""
    openid = models.CharField(
        max_length=64, unique=True, verbose_name='微信OpenID'
    )
    nickname = models.CharField(
        max_length=100, blank=True, verbose_name='昵称'
    )
    avatar_url = models.URLField(
        max_length=500, blank=True, verbose_name='头像URL'
    )
    session_key = models.CharField(
        max_length=100, blank=True, verbose_name='会话密钥'
    )

    class Meta:
        verbose_name = '微信用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.nickname or self.username} ({self.openid})"
