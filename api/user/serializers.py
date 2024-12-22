from django.core import exceptions
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.db.transaction import atomic

from rest_framework import serializers
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_registration.api.serializers import DefaultUserProfileSerializer
from drf_writable_nested import WritableNestedModelSerializer
from phonenumber_field.serializerfields import PhoneNumberField

from apps.utils.utils import get_object_or_none
from apps.user.models import User,ResetPasword,PhoneNumberChange


class RegisterUserSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    class Meta:
        fields = (
            'phone',
        )
    
    @atomic    
    def create(self, validated_data):
        _users = User.objects.filter(**validated_data)
        user = _users.first()

        if not _users.exists():
            user = User.objects.create(**validated_data)

        if not ResetPasword.objects.filter(user=user,is_active=True,is_test=True).exists():
            reset_codes = user.codes.all().delete()
            reset = ResetPasword.objects.create(user=user,is_active=True)

        return user 



class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    class Meta:
        fields = ['password','password_confirm']
   
    def validate(self, data):
        password = data.get('password')
        password_confirm = data.get('password_confirm')

        errors = dict()

        if password != password_confirm:
            errors['password_confirm'] = ['Passwords do not match.']

        try:
            validate_password(password)
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)

        return super(ResetPasswordSerializer, self).validate(data)



class GoogleAuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()

    def create(self, validated_data):
        try:
            tooken = id_token.verify_oauth2_token(
                validated_data['token'], requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID
            )
        except Exception as e:
            raise ValueError('Bad token Google')
        user, _ = User.objects.get_or_create(email=tooken.get('email',validated_data['email']),auth_provider=User.AUTH_PROVIDERS.get('google'))
        user.first_name=tooken.get('given_name',None)
        user.last_name = tooken.get('family_name',None)
        user.full_name = tooken.get('name',None)
        user.last_name=tooken.get('family_name',None)
        user.image_url=tooken.get('picture',None)
        user.save()
    
        return user



class UserSerializer(WritableNestedModelSerializer):
    password = serializers.CharField(validators=[validate_password],write_only=True,allow_null=True,required=False)
    
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ('last_login','date_joined')
        
    def create(self, validated_data):
        password = validated_data.pop('password',"defaultPassword")
        user:User = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user 
    
    def update(self, instance:User, validated_data):
        password = validated_data.pop('password',None)

        if password:
            instance.set_password(password)
            instance.save()

        return super().update(instance, validated_data)


class PhoneNumberChangeSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = PhoneNumberChange
        exclude = ['is_active','code','is_test']
    
    def validate_new_phone_number(self, value):
        if get_object_or_none(User, phone=value):
            raise serializers.ValidationError('Такой номер телефон уже зарегистрирован.')
        
        return value

    def create(self, validated_data):
        user = validated_data.get('user')
        print(user)
        
        reset_number = PhoneNumberChange.objects.filter(user=user,is_test=True)
        
        if reset_number.exists():
            return reset_number.first()
        
        phhon_numbers = user.phone_numbers.all().delete()

        return super().create(validated_data)
