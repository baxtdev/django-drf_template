from django_filters.rest_framework.filterset import FilterSet
import django_filters

from .serializers import User
 

class UserFilterSet(FilterSet):
    date_joined = django_filters.DateTimeFromToRangeFilter(
        field_name='date_joined',
        label='Диапазон дат регистрации'
    )
    month = django_filters.NumberFilter(
        field_name='date_joined',
        lookup_expr='month',
        label='Месяц регистрации'
    )
    day = django_filters.NumberFilter(
        field_name='date_joined',
        lookup_expr='day',
        label='День регистрации'
    )
    year = django_filters.NumberFilter(
        field_name='date_joined',
        lookup_expr='year',
        label='Год регистрации'
    )
    is_verified = django_filters.BooleanFilter(field_name='client__is_verify')

    class Meta:
        model = User
        fields = ['is_active','is_staff','is_superuser','gender','role','is_notifications','phone']