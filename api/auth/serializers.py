from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from apps.stations.models import GasStation
from apps.utils.utils import get_object_or_none

class LoginSerializer(serializers.Serializer):
    login = PhoneNumberField(required=True)
    password = serializers.CharField()
    gas_station = serializers.PrimaryKeyRelatedField(
        queryset=GasStation.objects.all(),
        allow_null=True,
        required=False,
        default=None,
        help_text='Опционально. Если указан, авторизация будет производиться с указанным адресом.'
    )
