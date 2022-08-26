from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db.models import CASCADE
from django_rest_passwordreset.tokens import get_token_generator

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


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField('email address', unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        'username',
        max_length=150,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text=
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ,
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=TYPE_OF_USER, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.email}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


class Shop(models.Model):
    url = models.CharField(max_length=50, null=True, blank=True, verbose_name='ссылка для обновления прайса')
    name = models.CharField(max_length=50, verbose_name='название')
    state = models.BooleanField(default=True, verbose_name='статус получения заказов')
    user = models.OneToOneField(User, verbose_name='Пользователь',
                                blank=True, null=True,
                                on_delete=models.CASCADE)

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
    shop = models.ForeignKey(Shop, on_delete=CASCADE, verbose_name='магазины', related_name='shops', blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    model = models.CharField(max_length=50, verbose_name='модель', )
    quantity = models.PositiveIntegerField(verbose_name='количество')
    price = models.PositiveIntegerField(verbose_name='цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена', default=0)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = "Список информации о продукте"
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop', 'external_id'], name='unique_product_info'),
        ]

    def __str__(self):
        return f'{self.product}'


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, verbose_name='Пользователь', related_name='contacts', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон',)
    city = models.CharField(max_length=20, verbose_name='Город', )
    street = models.CharField(max_length=20, verbose_name='Улица',)
    house = models.CharField(max_length=20, verbose_name='Дом',)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = "Список контактов"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, verbose_name='Пользователь', blank=True,
                             related_name='orders')
    dt = models.DateTimeField(auto_now_add=True, verbose_name='время заказа',)
    status = models.CharField(max_length=20, choices=STATE_CHOICES, verbose_name='статус заказа')
    contact = models.ForeignKey(Contact, on_delete=CASCADE, verbose_name='контакты', blank=True, null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"

    def __str__(self):
        return f'{self.user}, {self.dt}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=CASCADE, blank=True, verbose_name='заказ',
                              related_name='ordered_items')
    product_info = models.ForeignKey(ProductInfo, on_delete=CASCADE, verbose_name='информация о продукте', blank=True,
                                     related_name='ordered_items')
    quantity = models.PositiveIntegerField(verbose_name='количество', blank=True)

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item'),
        ]


class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = "Список имен параметров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='product_parameters', blank=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=100)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров"
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name="The User which is associated to this password reset token"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="When was this token generated"
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        "Key",
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)

