from django.urls import path
from shop import views


urlpatterns = [
    # 用户认证
    path('api/wechat-login/', views.wechat_login, name='wechat_login'),
    path('api/current-user/', views.get_current_user, name='get_current_user'),

    # 商品相关
    path('api/tags/', views.get_tags, name='get_tags'),
    path('api/goods/', views.get_goods, name='get_goods'),

    # 订单相关
    path('api/orders/create/', views.create_order, name='create_order'),
    path('api/orders/', views.get_orders, name='get_orders'),

    # 支付相关
    path('api/wechat-pay/', views.wechat_pay, name='wechat_pay'),
    path(
        'api/wechat-pay-notify/',
        views.wechat_pay_notify,
        name='wechat_pay_notify'
    ),
]
