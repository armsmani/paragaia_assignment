from django.contrib.auth import authenticate, logout, login as auth_login
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from django.conf import settings


def send_message(order_id, message):
    mirakl_headers = {'Authorization': settings.MIRAKL_API_KEY, 'Content-Type': 'multipart/form-data', 'Accept': 'multipart/form-data'}
    data = {"thread_input": {'body': message, 'topic': {'type': '20', 'value': 'Question about delivery'}, "to": ["shop"]}}
    send = requests.post('https://paragaia-dev.mirakl.net/api/orders/%s/threads' % order_id, headers=mirakl_headers, data=data)
    response = send.json()
    return response['message']


def read_api_data(max):
    data = {}
    mirakl_headers = {'Authorization': settings.MIRAKL_API_KEY}
    orders = requests.get('https://paragaia-dev.mirakl.net/api/orders/?max=%s' % max, headers=mirakl_headers)
    orders = orders.json()
    data['total_count'] = orders['total_count']
    orders_list = orders['orders']

    orders = []
    for order in orders_list:
        item = {}
        item['order_id'] = order['order_id']
        item['created_date'] = order['created_date']
        item['shop_name'] = order['shop_name']
        orders.append(item)
    data['orders'] = orders
    return data


def login(request):
    msg = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if User.objects.filter(username=username).exists():
            auth_login(request, user)
            return redirect('/dashboard/')
        else:
            msg = "Please provide valid login credentials."
    return render(request, 'login.html', {'msg': msg})


@login_required
def user_logout(request):
    logout(request)
    return redirect('/')


@login_required
@csrf_exempt
def dashboard(request):
    if request.is_ajax and request.method == "POST":
        send = send_message(request.POST.get('order_id'), request.POST.get('message'))
        return HttpResponse(json.dumps(send))
    next_max = 0
    if request.GET.get('max'):
        max = int(request.GET.get('max'))
    else:
        max = 10
    data = read_api_data(max)
    orders = data['orders']
    if int(data['total_count']) > max:
        next_max = max + 10
    return render(request, 'index.html', {'orders':orders, 'next_max':next_max, 'key':settings.MIRAKL_API_KEY, 'total_count':data['total_count']})
