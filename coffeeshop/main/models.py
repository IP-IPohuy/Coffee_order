from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Product(models.Model):
    product_name = models.CharField(max_length=50)
    product_price = models.IntegerField()
    product_description = models.TextField()
    is_available = models.BooleanField()

    def __str__(self):
        return self.product_name

class ProductInOrder(models.Model):  
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_orders')
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.product.product_name} (x{self.quantity})'

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('ready', 'Готов'),
        ('in_progress', 'Готовится'),
        ('cancelled', 'Отклонен'),
        ('completed', 'Завершен')
    ]
    order_status = models.CharField(choices=ORDER_STATUS_CHOICES, max_length=11)
    order_name = models.CharField(max_length=50)  
    order_content = models.ManyToManyField(ProductInOrder)  
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    time_created = models.TimeField(default=timezone.now)
    time_completed = models.TimeField(default=timezone.now)
    time_prepared = models.TimeField(default=timezone.now)

    def __str__(self):
        return f'Order {self.order_name} ({self.get_order_status_display()})'
