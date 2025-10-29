from django.urls import path
from shop import views


urlpatterns = [
    path('api/wechat-login/', views.wechat_login, name='wechat_login'),
    path('api/current-user/', views.get_current_user, name='get_current_user'),
]
