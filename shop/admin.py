from django.contrib import admin
from .models import WechatUser, Tag, Goods, Order


@admin.register(WechatUser)
class WechatUserAdmin(admin.ModelAdmin):
    """微信用户管理界面配置"""
    list_display = (
        'username', 'nickname', 'openid', 'email', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )
    search_fields = (
        'username', 'nickname', 'openid', 'email', 'first_name', 'last_name'
    )
    ordering = ('-date_joined',)
    readonly_fields = ('openid', 'session_key', 'date_joined', 'last_login')

    fieldsets = (
        ('基本信息', {
            'fields': (
                'username', 'nickname', 'email', 'first_name', 'last_name'
            )
        }),
        ('微信信息', {
            'fields': ('openid', 'avatar_url', 'session_key')
        }),
        ('权限状态', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('时间信息', {
            'fields': ('date_joined', 'last_login')
        }),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """商品标签管理界面配置"""
    list_display = ('name', 'is_active', 'sequence')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('sequence', 'name')
    list_editable = ('is_active', 'sequence')


@admin.register(Goods)
class GoodsAdmin(admin.ModelAdmin):
    """商品管理界面配置"""
    list_display = ('name', 'tag', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'tag', 'created_at')
    search_fields = ('name', 'desc')
    ordering = ('-created_at',)
    list_editable = ('is_active', 'price')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'tag', 'price', 'is_active')
        }),
        ('商品描述', {
            'fields': ('desc',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """订单管理界面配置"""
    list_display = (
        'order_number', 'user', 'goods', 'quantity', 'total_amount',
        'status', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'order_number', 'user__username', 'user__nickname',
        'goods__name', 'receiver_name', 'receiver_phone'
    )
    ordering = ('-created_at',)
    readonly_fields = (
        'order_number', 'total_amount', 'created_at', 'paid_at',
        'completed_at', 'transaction_id'
    )

    fieldsets = (
        ('订单信息', {
            'fields': (
                'order_number', 'user', 'goods', 'quantity', 'total_amount'
            )
        }),
        ('收货信息', {
            'fields': (
                'receiver_name', 'receiver_phone', 'receiver_address'
            )
        }),
        ('状态信息', {
            'fields': (
                'status', 'payment_method', 'prepay_id', 'transaction_id'
            )
        }),
        ('时间信息', {
            'fields': ('created_at', 'paid_at', 'completed_at')
        }),
    )
