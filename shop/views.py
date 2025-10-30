from django.forms import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import json
import requests
from shop.models import Tag, WechatUser, Goods, Order
import time
import hashlib
import xml.etree.ElementTree as ET
import random


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
            if not code:
                return JsonResponse({
                    'code': 400,
                    'message': '缺少必要参数: code'
                }, status=400)

            appid = 'wxd576896f718821dd'  # 替换为你的小程序AppID
            secret = '3d3719b287f359b54e8d310fb9e7fcb5'  # 替换为你的小程序AppSecret

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
                    'session_key': session_key
                }
            )

            if not created:
                if session_key:
                    user.session_key = session_key
                user.save()

            return JsonResponse({
                'code': 200,
                'message': '登录成功',
                'data': {
                    'openid': user.openid,
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


def get_current_user(request):
    """
    获取当前登录用户信息接口
    """
    if request.method == 'GET':
        openid = request.META.get('HTTP_AUTHORIZATION').replace('Bearer ', '')
        if not openid:
            return JsonResponse({
                'code': 401,
                'message': '用户未登录'
            }, status=401)

        try:
            user = WechatUser.objects.filter(openid=openid).first()
            return JsonResponse({
                'code': 200,
                'message': '获取用户信息成功',
                'data': {
                    'user_id': user.id,
                    'openid': user.openid,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None
                }
            })
        except WechatUser.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '用户不存在'
            }, status=404)

    return JsonResponse({
        'code': 405,
        'message': '方法不允许'
    }, status=405)


@csrf_exempt
def get_tags(request):
    tags = Tag.objects.filter(is_active=True).order_by('sequence').all()
    return JsonResponse({
        'code': 200,
        'data': [model_to_dict(tag) for tag in tags]
    })


@csrf_exempt
def get_goods(request):
    tag_id = request.GET.get('tag_id')
    goods = Goods.objects.filter(
        is_active=True, tag_id=tag_id).order_by('id').all()
    ret = []
    for good in goods:
        data = model_to_dict(good, exclude=['url'])
        if good.url:
            data['url'] = request.build_absolute_uri(good.url.url)
        else:
            data['url'] = None
        ret.append(data)
    return JsonResponse({
        'code': 200,
        'data': ret
    })


def get_user_from_session(request):
    """从session获取用户"""
    openid = request.META.get('HTTP_AUTHORIZATION').replace('Bearer ', '')
    if not openid:
        return None
    try:
        return WechatUser.objects.filter(openid=openid).first()
    except WechatUser.DoesNotExist:
        return None


@csrf_exempt
def create_order(request):
    """创建订单接口"""
    if request.method == 'POST':
        try:
            user = get_user_from_session(request)
            if not user:
                return JsonResponse({
                    'code': 401,
                    'message': '用户未登录'
                }, status=401)

            data = json.loads(request.body)
            goods_id = data.get('goods_id')
            quantity = data.get('quantity', 1)
            receiver_name = data.get('receiver_name')
            receiver_phone = data.get('receiver_phone')
            receiver_address = data.get('receiver_address')

            # 验证必填字段
            if not all([goods_id, receiver_name, receiver_phone,
                       receiver_address]):
                return JsonResponse({
                    'code': 400,
                    'message': '缺少必要参数'
                }, status=400)

            # 获取商品信息
            try:
                goods = Goods.objects.get(id=goods_id, is_active=True)
            except Goods.DoesNotExist:
                return JsonResponse({
                    'code': 404,
                    'message': '商品不存在'
                }, status=404)

            # 创建订单
            order = Order(
                user=user,
                goods=goods,
                quantity=quantity,
                receiver_name=receiver_name,
                receiver_phone=receiver_phone,
                receiver_address=receiver_address
            )
            order.save()

            return JsonResponse({
                'code': 200,
                'message': '订单创建成功',
                'data': {
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount)
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


@csrf_exempt
def get_orders(request):
    """获取用户订单列表"""
    if request.method == 'GET':
        try:
            user = get_user_from_session(request)
            if not user:
                return JsonResponse({
                    'code': 401,
                    'message': '用户未登录'
                }, status=401)

            orders = Order.objects.filter(
                user=user
            ).order_by('-created_at')

            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'goods_name': order.goods.name,
                    'quantity': order.quantity,
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'created_at': order.created_at.isoformat(),
                    'paid_at': order.paid_at.isoformat() if order.paid_at else None
                })

            return JsonResponse({
                'code': 200,
                'message': '获取订单列表成功',
                'data': orders_data
            })

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


@csrf_exempt
def wechat_pay(request):
    """微信支付接口"""
    if request.method == 'POST':
        try:
            user = get_user_from_session(request)
            if not user:
                return JsonResponse({
                    'code': 401,
                    'message': '用户未登录'
                }, status=401)

            data = json.loads(request.body)
            order_id = data.get('order_id')

            if not order_id:
                return JsonResponse({
                    'code': 400,
                    'message': '缺少订单ID'
                }, status=400)

            # 获取订单
            try:
                order = Order.objects.get(
                    id=order_id,
                    user=user,
                    status='pending'
                )
            except Order.DoesNotExist:
                return JsonResponse({
                    'code': 404,
                    'message': '订单不存在或状态不正确'
                }, status=404)

            # 微信支付配置（实际项目中应从环境变量获取）
            appid = 'YOUR_WECHAT_APPID'
            mch_id = 'YOUR_MCH_ID'
            api_key = 'YOUR_API_KEY'

            # 生成预支付订单
            nonce_str = ''.join(
                random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32)
            )
            body = f"商品购买 - {order.goods.name}"
            out_trade_no = order.order_number
            total_fee = int(order.total_amount * 100)  # 转换为分
            spbill_create_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            notify_url = 'http://your-domain.com/shop/wechat_pay_notify/'
            trade_type = 'JSAPI'
            openid = user.openid

            # 生成签名
            params = {
                'appid': appid,
                'mch_id': mch_id,
                'nonce_str': nonce_str,
                'body': body,
                'out_trade_no': out_trade_no,
                'total_fee': total_fee,
                'spbill_create_ip': spbill_create_ip,
                'notify_url': notify_url,
                'trade_type': trade_type,
                'openid': openid
            }

            # 按参数名ASCII码从小到大排序
            sorted_params = sorted(params.items())
            sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
            sign_str += f"&key={api_key}"
            sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

            # 构建XML请求数据
            xml_data = f"""<xml>
<appid>{appid}</appid>
<mch_id>{mch_id}</mch_id>
<nonce_str>{nonce_str}</nonce_str>
<body>{body}</body>
<out_trade_no>{out_trade_no}</out_trade_no>
<total_fee>{total_fee}</total_fee>
<spbill_create_ip>{spbill_create_ip}</spbill_create_ip>
<notify_url>{notify_url}</notify_url>
<trade_type>{trade_type}</trade_type>
<openid>{openid}</openid>
<sign>{sign}</sign>
</xml>"""

            # 调用微信支付统一下单API
            wechat_pay_url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
            response = requests.post(
                wechat_pay_url, data=xml_data.encode('utf-8'))

            # 解析响应
            root = ET.fromstring(response.content)
            return_code = root.find('return_code').text
            result_code = root.find('result_code').text

            if return_code == 'SUCCESS' and result_code == 'SUCCESS':
                prepay_id = root.find('prepay_id').text

                # 保存预支付ID到订单
                order.prepay_id = prepay_id
                order.save()

                # 生成前端支付参数
                timestamp = str(int(time.time()))
                package = f"prepay_id={prepay_id}"
                nonce_str = ''.join(
                    random.choices(
                        'abcdefghijklmnopqrstuvwxyz0123456789', k=32)
                )

                # 生成支付签名
                pay_params = {
                    'appId': appid,
                    'timeStamp': timestamp,
                    'nonceStr': nonce_str,
                    'package': package,
                    'signType': 'MD5'
                }
                sorted_pay_params = sorted(pay_params.items())
                pay_sign_str = '&'.join(
                    [f"{k}={v}" for k, v in sorted_pay_params])
                pay_sign_str += f"&key={api_key}"
                pay_sign = hashlib.md5(
                    pay_sign_str.encode('utf-8')
                ).hexdigest().upper()

                return JsonResponse({
                    'code': 200,
                    'message': '支付参数生成成功',
                    'data': {
                        'appId': appid,
                        'timeStamp': timestamp,
                        'nonceStr': nonce_str,
                        'package': package,
                        'signType': 'MD5',
                        'paySign': pay_sign
                    }
                })
            else:
                error_msg = root.find('return_msg').text
                return JsonResponse({
                    'code': 400,
                    'message': f'微信支付下单失败: {error_msg}'
                }, status=400)

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


@csrf_exempt
def wechat_pay_notify(request):
    """微信支付回调接口"""
    if request.method == 'POST':
        try:
            # 解析XML数据
            xml_data = request.body.decode('utf-8')
            root = ET.fromstring(xml_data)

            # 验证签名
            params = {}
            for child in root:
                if child.tag != 'sign':
                    params[child.tag] = child.text

            # 按参数名ASCII码从小到大排序
            sorted_params = sorted(params.items())
            sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
            sign_str += f"&key=YOUR_API_KEY"  # 使用你的API密钥

            calculated_sign = hashlib.md5(
                sign_str.encode('utf-8')
            ).hexdigest().upper()

            received_sign = root.find('sign').text

            if calculated_sign != received_sign:
                return JsonResponse({
                    'return_code': 'FAIL',
                    'return_msg': '签名验证失败'
                }, content_type='application/xml')

            # 处理支付结果
            return_code = root.find('return_code').text
            result_code = root.find('result_code').text
            out_trade_no = root.find('out_trade_no').text
            transaction_id = root.find('transaction_id').text

            if return_code == 'SUCCESS' and result_code == 'SUCCESS':
                # 更新订单状态
                try:
                    order = Order.objects.get(order_number=out_trade_no)
                    order.status = 'paid'
                    order.transaction_id = transaction_id
                    order.paid_at = timezone.now()
                    order.save()

                    # 返回成功响应
                    response_xml = """<xml>
<return_code><![CDATA[SUCCESS]]></return_code>
<return_msg><![CDATA[OK]]></return_msg>
</xml>"""
                    return HttpResponse(response_xml, content_type='application/xml')

                except Order.DoesNotExist:
                    response_xml = """<xml>
<return_code><![CDATA[FAIL]]></return_code>
<return_msg><![CDATA[订单不存在]]></return_msg>
</xml>"""
                    return HttpResponse(response_xml, content_type='application/xml')

            else:
                response_xml = """<xml>
<return_code><![CDATA[FAIL]]></return_code>
<return_msg><![CDATA[支付失败]]></return_msg>
</xml>"""
                return HttpResponse(response_xml, content_type='application/xml')

        except Exception as e:
            response_xml = f"""<xml>
<return_code><![CDATA[FAIL]]></return_code>
<return_msg><![CDATA[{str(e)}]]></return_msg>
</xml>"""
            return HttpResponse(response_xml, content_type='application/xml')

    return JsonResponse({
        'code': 405,
        'message': '方法不允许'
    }, status=405)
