from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
import json
import requests
from .models import WechatUser


@csrf_exempt
def wechat_login(request):
    """
    微信小程序登录接口
    接收小程序传来的code，调用微信API获取openid和session_key
    创建或更新用户信息
    """
    if request.method == 'POST':
        try:
            # 解析请求数据
            data = json.loads(request.body)
            code = data.get('code')
            nickname = data.get('nickname', '')
            avatar_url = data.get('avatar_url', '')

            if not code:
                return JsonResponse({
                    'code': 400,
                    'message': '缺少必要参数: code'
                }, status=400)

            # 这里需要配置你的微信小程序AppID和AppSecret
            # 在实际项目中，请将这些敏感信息存储在环境变量中
            appid = 'YOUR_WECHAT_APPID'  # 替换为你的小程序AppID
            secret = 'YOUR_WECHAT_SECRET'  # 替换为你的小程序AppSecret

            # 调用微信API获取openid和session_key
            wechat_api_url = (
                f'https://api.weixin.qq.com/sns/jscode2session?'
                f'appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code'
            )

            response = requests.get(wechat_api_url)
            wechat_data = response.json()

            if 'openid' not in wechat_data:
                return JsonResponse({
                    'code': 401,
                    'message': '微信登录失败',
                    'error': wechat_data.get('errmsg', '未知错误')
                }, status=401)

            openid = wechat_data['openid']
            session_key = wechat_data.get('session_key', '')

            # 查找或创建用户
            user, created = WechatUser.objects.get_or_create(
                openid=openid,
                defaults={
                    'username': openid,
                    'nickname': nickname,
                    'avatar_url': avatar_url,
                    'session_key': session_key
                }
            )

            # 如果用户已存在，更新用户信息
            if not created:
                if nickname:
                    user.nickname = nickname
                if avatar_url:
                    user.avatar_url = avatar_url
                if session_key:
                    user.session_key = session_key
                user.save()

            # 登录用户
            login(request, user)

            return JsonResponse({
                'code': 200,
                'message': '登录成功',
                'data': {
                    'user_id': user.id,
                    'openid': user.openid,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'is_new_user': created
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'code': 405,
        'message': '方法不允许'
    }, status=405)


@login_required
@csrf_exempt
def get_current_user(request):
    """
    获取当前登录用户信息接口
    """
    if request.method == 'GET':
        user = request.user

        return JsonResponse({
            'code': 200,
            'message': '获取用户信息成功',
            'data': {
                'user_id': user.id,
                'openid': user.openid,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })

    return JsonResponse({
        'code': 405,
        'message': '方法不允许'
    }, status=405)
