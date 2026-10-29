import django_filters
from .models import Payment

class PaymentFilter(django_filters.FilterSet):
    course = django_filters.NumberFilter(field_name='course__id')
    lesson = django_filters.NumberFilter(field_name='lesson__id')
    payment_method = django_filters.CharFilter(field_name='payment_method', lookup_expr='iexact')

    class Meta:
        model = Payment
        fields = ['course', 'lesson', 'payment_method']
