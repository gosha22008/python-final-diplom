from django.shortcuts import render
from rest_framework import generics, viewsets

# Create your views here.


from .models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact
from .serializers import ProductSerializer, CategorySerializer, ShopSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

