from django.contrib import admin
from .models import WechatUser


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
