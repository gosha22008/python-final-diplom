"""orders URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from backend.views import ProductViewSet, CategoryViewSet, ShopViewSet, OrderViewSet, ProductInfoViewSet, \
    OrderItemViewSet, ContactViewSet, RegisterAccount, LoginAccount, PartnerUpdate, ProductInfoView, PartnerState, \
    ContactView, AccountDetails, BasketView, PartnerOrders, OrderView
from rest_framework import routers


router = routers.SimpleRouter()
router.register(r'product', ProductViewSet)
router.register(r'category', CategoryViewSet)
router.register(r'shop', ShopViewSet)
router.register(r'productinfo', ProductInfoViewSet)
router.register(r'orderitem', OrderItemViewSet)
router.register(r'contact', ContactViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/v1/', include(router.urls)),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/account', AccountDetails.as_view(), name='user-account'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('product/search', ProductInfoView.as_view(), name='product-search'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),

] + router.urls
