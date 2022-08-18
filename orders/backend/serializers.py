from rest_framework import serializers
from .models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact, User, ProductParameter


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['user', 'phone', 'city', 'street', 'house', 'structure', 'building', 'apartment']


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name', 'state',)
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    shops = ShopSerializer(many=True)

    class Meta:
        model = Category
        fields = ['name', 'shops']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['name', 'category']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    product_parameters = ProductParameterSerializer(read_only=True, many=True)
    shop = ShopSerializer()

    class Meta:
        model = ProductInfo
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer()

    class Meta:
        model = OrderItem
        fields = ['order', 'product_info', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer()

    class Meta:
        model = Order
        fields = ['id', 'user', 'dt', 'status', 'order_item']
        read_only_fields = ['user']
