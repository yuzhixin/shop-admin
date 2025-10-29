from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor_uploader.fields import RichTextUploadingField
import time
import random


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


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, verbose_name='标签名称')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    sequence = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '商品标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Goods(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name='商品名称')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='价格'
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name='商品标签'
    )

    desc = RichTextUploadingField()  # 支持图片上传

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='更新时间'
    )

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Order(models.Model):
    """订单模型"""
    ORDER_STATUS_CHOICES = (
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('wechat', '微信支付'),
    )

    id = models.AutoField(primary_key=True)
    order_number = models.CharField(
        max_length=32, unique=True, verbose_name='订单号'
    )
    user = models.ForeignKey(
        WechatUser, on_delete=models.CASCADE, verbose_name='用户'
    )
    goods = models.ForeignKey(
        Goods, on_delete=models.CASCADE, verbose_name='商品'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='总金额'
    )

    # 收货信息
    receiver_name = models.CharField(max_length=50, verbose_name='收货人姓名')
    receiver_phone = models.CharField(max_length=20, verbose_name='收货人手机')
    receiver_address = models.TextField(verbose_name='收货地址')

    # 订单状态
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending',
        verbose_name='订单状态'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='wechat',
        verbose_name='支付方式'
    )

    # 支付信息
    prepay_id = models.CharField(
        max_length=64, blank=True, null=True, verbose_name='预支付ID'
    )
    transaction_id = models.CharField(
        max_length=64, blank=True, null=True, verbose_name='微信交易号'
    )

    # 时间信息
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='创建时间'
    )
    paid_at = models.DateTimeField(
        null=True, blank=True, verbose_name='支付时间'
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name='完成时间'
    )

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.goods.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{int(time.time())}{random.randint(1000, 9999)}"
        if not self.total_amount:
            self.total_amount = self.goods.price * self.quantity
        super().save(*args, **kwargs)
