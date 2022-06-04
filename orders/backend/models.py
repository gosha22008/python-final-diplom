from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, User
from django.contrib.auth.validators import UnicodeUsernameValidator

# Create your models here.
from django.db.models import CASCADE

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

TYPE_OF_USER = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель')
)


class Shop(models.Model):
    url = models.CharField(max_length=50, null=True, blank=True, verbose_name='ссылка для обновления прайса')
    name = models.CharField(max_length=50, verbose_name='название')
    state = models.BooleanField(default=True, verbose_name='статус получения заказов')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='название')
    shops = models.ManyToManyField(Shop, related_name='categories', verbose_name='Магазины')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    category = models.ForeignKey(Category, on_delete=CASCADE, verbose_name='Категория', related_name='products')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=CASCADE, verbose_name='название', related_name='product_infos')
    shop = models.ForeignKey(Shop, on_delete=CASCADE, verbose_name='магазины', related_name='shops', blank=True, null=True)
    model = models.CharField(max_length=50,)
    quantity = models.PositiveIntegerField(verbose_name='количество')
    price = models.PositiveIntegerField(verbose_name='цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = "Список информации о продукте"


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, verbose_name='Пользователь', blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон', blank=True)
    city = models.CharField(max_length=20, verbose_name='Город', blank=True)
    street = models.CharField(max_length=20, verbose_name='Улица', blank=True)
    house = models.CharField(max_length=20, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = "Список контактов"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, verbose_name='Пользователь', blank=True, null=True)
    dt = models.DateTimeField(auto_now_add=True, verbose_name='время заказа',)
    status = models.CharField(max_length=20, choices=STATE_CHOICES, verbose_name='статус заказа', blank=True)
    contact = models.ForeignKey(Contact, on_delete=CASCADE, verbose_name='контакты', blank=True, null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"

    def __str__(self):
        return self.dt


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=CASCADE, blank=True, null=True, verbose_name='заказ')
    product_info = models.ForeignKey(ProductInfo, on_delete=CASCADE, verbose_name='информация о продукте', blank=True, null=True)
    quantity = models.PositiveIntegerField(verbose_name='количество', blank=True)

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
