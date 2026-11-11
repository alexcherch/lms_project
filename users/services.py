import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name, description=None):
    """
    Создает продукт в Stripe.
    Возвращает объект продукта.
    """
    product = stripe.Product.create(
        name=name,
        description=description,
    )
    return product


def create_stripe_price(product_id, amount):
    """
    Создает цену для продукта в Stripe.
    amount — сумма в рублях (конвертируем в копейки, умножая на 100).
    """
    price = stripe.Price.create(
        product=product_id,
        unit_amount=int(amount * 100),  # Stripe принимает копейки
        currency="rub",
    )
    return price


def create_stripe_session(price_id, success_url, cancel_url):
    """
    Создает сессию для оплаты в Stripe.
    Возвращает объект сессии (в нем будет ссылка на оплату).
    """
    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session


def get_stripe_session_status(session_id):
    """
    Получает данные о сессии по её ID из Stripe.
    """
    session = stripe.checkout.Session.retrieve(session_id)
    return session
