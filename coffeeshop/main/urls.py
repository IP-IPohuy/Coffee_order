from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('display', views.display, name='display'),
    path('get-ordres', views.get_orders, name='get_orders'),
    path('worker_panel', views.worker_panel, name='worker_panel'),
    path('', views.sign_in, name='sign_in'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('orders/complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('orders_history', views.orders_history, name='orders_history'),
    path('orders/mark_ready/<int:order_id>/', views.mark_order_ready, name='mark_order_ready'),
    path('orders/add/', views.add_order, name='add_order'),
    path('additional_panel', views.additional_panel, name='additional_panel'),
    path('add_product', views.add_product, name='add_product'),
    path('startshift', views.startshift, name='startshift'),
]