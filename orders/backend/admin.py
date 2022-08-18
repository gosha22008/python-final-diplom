from django.contrib import admin
from .models import Category, Product, ProductInfo, Order, OrderItem, Contact, Shop, User


# Register your models here.
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # list_display = ['id', 'name']
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # list_display = ['id', 'name', 'category']
    pass


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    # list_display = ['id', 'product', 'name', 'price', 'quantity']
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # list_display = ['id', 'dt', 'status']
    pass


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass





