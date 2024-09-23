from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from main.models import Order, Product, ProductInOrder, Shift
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
                return redirect('startshift')  
        else:
            error = 'Неправильное имя пользователя или пароль'
    else:
        form = CustomLoginForm()

    return render(request, 'main/sign_in.html', {'form': form, 'error': error})

@login_required
def startshift(request):
    if request.method == 'POST':

        products = Product.objects.filter(count_type='non-inf')
        for product in products:
            stock_value = request.POST.get(f'stock_{product.id}')
            if stock_value is not None:
                product.stock = int(stock_value)
                product.save()
        

        Shift.objects.create(date=timezone.now(), is_active=True)

        return redirect('worker_panel') 
    now = timezone.now()
    products = Product.objects.filter(count_type='non-inf')  # Товары с ограниченным количеством
    return render(request, 'main/startshift.html', {'products': products, 'now': now})

@login_required
def worker_panel(request):
    message = None
    orders_in_progress = Order.objects.filter(order_status='in_progress')
    orders_ready = Order.objects.filter(order_status='ready')
    try:
        shift = get_object_or_404(Shift, is_active=True)
    except:
        active_shifts = Shift.objects.filter(is_active=True)
        for shift in active_shifts:
            if shift.date != timezone.now().date():
                shift.is_active = False
                message = f'Смена от {shift.date} не была закрыта.'
                shift.save()
    if request.method == 'POST':
        shift.is_active = False
        shift.save()

        return render(request, 'main/end_of_shift.html')
    

    print(message)
    return render(request, 'main/worker_panel.html', {'orders_in_progress': orders_in_progress, 'orders_ready': orders_ready, 'shift': shift, 'message': message})

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
        products = request.POST.getlist('products')  
        quantities = request.POST.getlist('quantities')  

        order = Order(order_name=order_name, order_status='in_progress', time_created=timezone.now())
        order.save()

        for product_id, quantity in zip(products, quantities):
            product = Product.objects.get(id=product_id)
            product_in_order = ProductInOrder(product=product, quantity=quantity)
            if product.count_type == 'non-inf':
                product.stock -= 1
                product.save()
            product_in_order.save()
            order.order_content.add(product_in_order)

        order.save()
        return redirect('worker_panel')

    products = Product.objects.filter(is_available=True)
    return render(request, 'main/add_order.html', {'products': products})

@login_required
def additional_panel(request):
    return render(request, 'main/additional_panel.html')

@login_required
def add_product(request):
    product_name = request.POST.get('product_name')  
    product_price = request.POST.get('product_price')  
    return render(request, 'main/add_product.html')


