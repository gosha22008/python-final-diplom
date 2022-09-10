from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from yaml import load, FullLoader

from backend.models import ConfirmEmailToken, User, Shop, Category, ProductInfo, Product, Parameter, ProductParameter
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created


@shared_task()
def send_email_token_reset_pass_task(user, key, user_email, *args, **kwargs):
    msg = EmailMultiAlternatives(
        # title:
        f"Токен для сброса пароля для {user}",
        # message:
        key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user_email]
    )
    msg.send()
    return True


@receiver(reset_password_token_created)
def password_reset_token_created_task(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    user = str(reset_password_token.user)
    key = str(reset_password_token.key)
    user_email = str(reset_password_token.user.email)
    send_email_token_reset_pass_task.delay(user, key, user_email)


@shared_task()
def send_email_new_user_registered_task(user_id, *args, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Подтверждение почты для {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()
    return True


@shared_task()
def send_email_new_order_task(user_id, *args, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        'Заказ сформирован, спасибо за заказ!',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()
    return True


@shared_task()
def do_import_task(*args, **kwargs):
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
    return True

