import functools
from distutils.util import strtobool
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


class ProductInfoViewSet(viewsets.ModelViewSet):
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    # permission_classes = [IsOwnerOrReadOnly]


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
        if not request.user.is_authenticated:
            return JsonResponse({"Status": False, "Error": "Oshibka auth"})

        if request.user.type != "shop":
            return JsonResponse({"Status": False, "Error": "Tolko dlya Shop"})

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
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                                        parameter_id=parameter.id,
                                                                        value=param_val)

            return JsonResponse({"Status": True})
        else:
            return JsonResponse({"Status": False, "Error": "Oshibka pyti"})


class ProductInfoView(APIView):
    """
    Класс поиска товаров
    """
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


class ContactView(APIView):
    """
    Класс для работы с контактами покупателей
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'phone', 'city', 'street', 'house'}.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"Status": True})
            else:
                return JsonResponse({"Status": False, "Error": serializer.errors})
        else:
            return JsonResponse({"Status": False})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'contact_id'}.issubset(request.data):
            if type(request.data['contact_id']) == int:
                contact = Contact.objects.filter(id=request.data['contact_id'], user=request.user.id).first()

                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({"Status": True})

                    return JsonResponse({"Status": False, "Error": serializer.errors})

        return JsonResponse({"Status": False, "Error": 'ne vse argumenti'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'contact_id'}.issubset(request.data):

            if type(request.data['contact_id']) == int:
                contact = Contact.objects.filter(id=request.data['contact_id'], user=request.user.id).first()

                if contact:
                    contact.delete()
                    return JsonResponse({"Status": True})

        return JsonResponse({"Status": False})


class AccountDetails(APIView):
    """
    Класс для работы данными пользователя
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(data=serializer.data)

    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'password'}.issubset(request.data):
            errors = []
            try:
                validate_password(request.data['password'])
            except Exception as error:
                for er in error:
                    errors.append(er)
                    return JsonResponse({"Status": False, "Error": {"password": errors}})
            else:
                request.user.set_password(request.data['password'])

            serializer = UserSerializer(request.user, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"Status": True})

        return JsonResponse({"Status": False})


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """
    # добавление товаров в корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_string = request.data.get('items')
        if items_string:
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            objects_created = 0
            for item in items_string:
                item.update({'order': basket.id})
                serializer = OrderItemSerializer(data=item)

                if serializer.is_valid():
                    try:
                        serializer.save()
                    except Exception as error:
                        return JsonResponse({'Status': False, 'Errors': str(error)})
                    else:
                        objects_created += 1
                else:
                    JsonResponse({'Status': False, 'Errors': serializer.errors})

            return JsonResponse({'Status': True, 'Создано объектов': objects_created})

        return JsonResponse({"Status": False})

    # Получтить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # редактировать количнество товаров
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items = request.data.get('items')

        if items:
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            objects_updated = 0
            for item in items:
                if type(item['id']) == int and type(item['quantity']) == int:
                    objects_updated += OrderItem.objects.filter(order_id=basket.id, product_info_id=item['id']).update(
                        quantity=item['quantity'])
            return JsonResponse({"Status": True, "Updates_objects_count": objects_updated})

        return JsonResponse({"Status": False})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items = request.data.get('items')

        if items:
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            print(basket)
            if basket:
                objects_deleted = 0
                for item_id in items:
                    if type(item_id) == int:
                        objects_deleted += OrderItem.objects.filter(order_id=basket.id,
                                                                    product_info_id=item_id).delete()[0]
                return JsonResponse({"Status": True, "Objects_deleted": objects_deleted})

        return JsonResponse({"Status": False})


class PartnerOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        order = Order.objects.filter(user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)

        return Response(serializer.data)


class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        order = Order.objects.filter(user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            if type(request.data['id']) == int:
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        status='new')
                except Exception as error:
                    return JsonResponse({'Status': False, 'Errors': str(error)})
                else:
                    if is_updated:
                        #new_order.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
