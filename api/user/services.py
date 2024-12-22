from django.db.models import Count,F,Aggregate,Sum
from django.utils.timezone import now
from django.db.transaction import atomic

from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from .serializers import ResetPasword,\
    UserSerializer,\
    PhoneNumberChange,PhoneNumberChangeSerializer


class UserModelService:
    
    def get_queryset(self):
        queryset=super().get_queryset()
        return queryset.exclude(id=self.request.user.id)



class ResetPasswordService:
    def get_object(self):
        try:
            return self.queryset.get(code=self.kwargs['code'])
        
        except ResetPasword.DoesNotExist:
            raise NotFound("Код не поддерживается")


    def post(self, request, *args, **kwargs):
        reset_object = self.get_object()
        current_time = now()
        time_diff = current_time - reset_object.date
        user = reset_object.user
        
        if not reset_object.is_test and time_diff.total_seconds() < 360:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            password = serializer.validated_data.get('password')
            user.set_password(password)
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)
            reset_object.delete()

            return Response({"detail": "Пароль успешно изменен", "token": token.key}, status=201)

        if reset_object.is_test:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"detail": "Пароль успешно изменен", "token": token.key}, status=201)

        reset_object.delete()
        return Response({"detail": "Этот код не активен"}, status=404)


class PhoneNumberChangeService:

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_object(self):
        code = self.kwargs.get('code')
        try:
            change_object = self.get_queryset().get(code=code)
            return change_object
        except PhoneNumberChange.DoesNotExist:
            raise NotFound(detail="Такого кода не существует")

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Phone number updated and token created",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description="message"),
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="Auth token")
                    }
                )
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='send-code')
    @atomic
    def send_code(self, request, *args, **kwargs) -> Response:
        change_object:PhoneNumberChange = self.get_object()
        if not change_object.is_test:
            current_time = now()
            time_diff = current_time - change_object.created_at

            if time_diff.total_seconds() > 180:
                change_object.delete()
                return Response({"detail": "Код просрочен или не активен."}, status=status.HTTP_400_BAD_REQUEST)

            user = change_object.user
            user.phone = change_object.new_phone_number
            user.save(update_fields=['phone'])

            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)

            change_object.delete()

            return Response({"detail": "Номер телефона успешно изменен", "token": token.key})

        user = change_object.user
        user.phone = change_object.new_phone_number
        user.save(update_fields=['phone'])
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({"detail": "Номер телефона успешно изменен", "token": token.key})

    