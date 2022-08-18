import functools
import time
from distutils.util import strtobool
from django.db import connection, reset_queries
from rest_framework.filters import SearchFilter
from yaml import load, Loader, FullLoader
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.db.models import Q, Sum, F
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse
from .models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact, Parameter, ProductParameter
from .permissions import IsOwnerOrReadOnly
from .serializers import ProductSerializer, CategorySerializer, ShopSerializer, OrderSerializer, \
    ProductInfoSerializer, OrderItemSerializer, ContactSerializer, UserSerializer


def query_debugger(func):
    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(' ---------------------- ')
        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.2f}s")
        print(' ---------------------- ')
        return result

    return inner_func


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # permission_classes = [IsOwnerOrReadOnly]

    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)


class ProductInfoViewSet(viewsets.ModelViewSet):
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    # permission_classes = [IsOwnerOrReadOnly]

    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class RegisterAccount(APIView):
    """
    Класс регистрации пользователя
    """
    def post(self, request, *args, **kwargs):
        if {'email', 'password', }.issubset(request.data):
            try:
                validate_password(request.data["password"])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                user_serialize = UserSerializer(data=request.data)
                if user_serialize.is_valid():
                    user = user_serialize.save()
                    user.set_password(request.data["password"])
                    user.save()
                    return JsonResponse({"Status": True, "user": f"{user}"})
                else:
                    return JsonResponse({"Status": False, "Error": user_serialize.errors})
        else:
            return JsonResponse({"Status": False, "Error": "Nevernie argumenti"})


class LoginAccount(APIView):
    """
    Класс авторизации пользователя
    """
    def post(self, request, *args, **kwargs):
        print(request.user)
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            print(user)
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, "Token": token.key})
            return JsonResponse({'Status': False, 'Errors': 'Ne ydalos avtorizovat'})
        return JsonResponse({'Status': False, 'Errors': 'Ne ykazani vse neobhodimie argumenti'})


class PartnerUpdate(APIView):
    """
    Класс обновления прайса
    """
    def post(self, request, *args, **kwargs):
        print(request.data, request.user, request.user.id, request.auth, request.content_type)
        if not request.user.is_authenticated:
            return JsonResponse({"Status": False, "Error": "Oshibka auth"})
        if request.user.type != "shop":
            return JsonResponse({"Status": False, "Error": "Tolko dlya Shop"})
        print(vars(request.user))
        if settings.PATH_TO_FILE:
            with open(settings.PATH_TO_FILE) as fh:
                # Load YAML data from the file
                read_data = load(fh, Loader=FullLoader)
            shop, _ = Shop.objects.get_or_create(name=read_data['shop'])
            for cate_gory in read_data['categories']:
                category, _ = Category.objects.get_or_create(id=cate_gory['id'], name=cate_gory['name'])
                category.shops.add(shop.id)
                category.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in read_data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              shop_id=shop.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              quantity=item['quantity'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'])
                    for param_name, param_val in item['parameters'].items():
                        parameter, _ = Parameter.objects.get_or_create(name=param_name)
                        product_param = ProductParameter.objects.create(product_info_id=product_info.id,
                                                                        parameter_id=parameter.id,
                                                                        value=param_val)

            return JsonResponse({"Status": True})
        else:
            return JsonResponse({"Status": False, "Error": "Oshibka pyti"})


class ProductInfoView(APIView):
    """
    Класс поиска товаров
    """
    @query_debugger
    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)
        # shop_id = request.GET.get('shop_id')
        # category_id = request.query_params.get('category_id')
        #
        # if shop_id:
        #     query = query & Q(shop_id=shop_id)
        #
        # if category_id:
        #     query = query & Q(product__category_id=category_id)
        #
        # queryset = ProductInfo.objects.filter(
        #     query).select_related(
        #     'shop', 'product__category').prefetch_related(
        #     'product_parameters__parameter').distinct()
        # serializer = ProductInfoSerializer(queryset, many=True)
        product_name = request.query_params.get('product_name')
        if product_name:
            query = query & Q(product__name__icontains=product_name)
        queryset = ProductInfo.objects.filter(query).select_related(
            "shop", "product").prefetch_related(
            'product_parameters__parameter')
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика
    """
    # получить текущий статус
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Only for shops!'}, status=403)

        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({"Status": True, "state": state})
            except ValueError as error:
                return JsonResponse({"Status": False, "Error": f'{str(error)}'})
        else:
            return JsonResponse({"Status": False, "Error": "Ne vse argumenti"})



