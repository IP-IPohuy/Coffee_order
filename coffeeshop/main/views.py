from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from main.models import Order, Product, ProductInOrder
from django.http import JsonResponse
from django.utils import timezone
from .forms import CustomLoginForm

def display(request):
    orders_in_progress = Order.objects.filter(order_status='in_progress')
    orders_ready = Order.objects.filter(order_status='ready')
    return render(request, 'main/display.html', {'orders_in_progress': orders_in_progress, 'orders_ready': orders_ready})

def get_orders(request):
    orders_in_progress = list(Order.objects.filter(order_status='in_progress').values('order_name'))
    orders_ready = list(Order.objects.filter(order_status='ready').values('order_name'))

    return JsonResponse({
        'orders_in_progress': orders_in_progress,
        'orders_ready': orders_ready,
    })

def sign_in(request):
    error = None
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('worker_panel')  
        else:
            error = 'Неправильное имя пользователя или пароль'
    else:
        form = CustomLoginForm()

    return render(request, 'main/sign_in.html', {'form': form, 'error': error})

@login_required
def worker_panel(request):
    orders_in_progress = Order.objects.filter(order_status='in_progress')
    orders_ready = Order.objects.filter(order_status='ready')
    return render(request, 'main/worker_panel.html', {'orders_in_progress': orders_in_progress, 'orders_ready': orders_ready})

@csrf_exempt
def complete_order(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            order.order_status = 'completed'  
            order.time_completed = timezone.now()
            order.save()
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def mark_order_ready(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            order.order_status = 'ready' 
            order.time_prepared = timezone.now()
            order.save()
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def orders_history(request):
    completed_orders = Order.objects.all().filter(order_status='completed')
    return render(request, 'main/orders_history.html', {'completed_orders': completed_orders})



@login_required
def add_order(request):
    if request.method == 'POST':
        order_name = request.POST.get('order_name')
        products = request.POST.getlist('products')  # Список выбранных продуктов
        quantities = request.POST.getlist('quantities')  # Список количеств

        order = Order(order_name=order_name, user=request.user, order_status='in_progress', time_created=timezone.now())
        order.save()

        for product_id, quantity in zip(products, quantities):
            product = Product.objects.get(id=product_id)
            product_in_order = ProductInOrder(product=product, quantity=quantity)
            product_in_order.save()
            order.order_content.add(product_in_order)

        order.save()
        return redirect('worker_panel')

    products = Product.objects.filter(is_available=True)
    return render(request, 'main/add_order.html', {'products': products})
