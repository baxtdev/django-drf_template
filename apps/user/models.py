from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password,check_password
from django.core.exceptions import ObjectDoesNotExist

from django_resized import ResizedImageField
from phonenumber_field.modelfields import PhoneNumberField

from apps.utils.models import TimeStampAbstractModel
from apps.utils.utils import generate_code,generate_string_code
from .managers import UserManager

class User(AbstractUser):
    phone=PhoneNumberField(
        'Телефон',
        unique=True,
    )
    image = ResizedImageField(
        upload_to='avatars/', 
        force_format='WEBP', 
        quality=90, 
        verbose_name="Фото",
        blank=True,
        null=True,
    ) 
    username = None
    middle_name = models.CharField(
        max_length=255, 
        verbose_name='Отчество',
        blank=True,
        null=True
        )
    last_activity = models.DateTimeField(
        verbose_name=_('last'),
        editable=True,
        blank=True,
        null=True
    )
    email = models.EmailField(
        _("Эл.почта"), 
        max_length=254,
        unique = True,
        blank=True,
        null=True
        )
    ADMIN = 'ADMIN'
    CLIENT = 'CLIENT'
    OTHER = 'MANG'
    ROLE_CHOICE=(
        (ADMIN,"Директор"),
        (CLIENT,"Клиент"),
        (OTHER,"Другое"),
    )
    role = models.CharField(
        choices = ROLE_CHOICE,
        max_length = 50,
        default = CLIENT,
    )
    GENDER_CHOICE = (
        ("M","Мужчина"),
        ("W","Женщина"),
        ("OTHER","Другое"),
        ("NONE","Не указан"),
    )
    gender = models.CharField(
        _("Пол"),
        choices = GENDER_CHOICE,
        max_length = 50,
        default = "NONE",
        blank=True,
        )
    date_of_birth = models.DateField(
        verbose_name=_('Дата рождения'),
        blank=True,
        null=True,
    )
    is_notifications = models.BooleanField(
        _('Отправлять уведомления'),
        default=False,
    )
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'phone'

    objects = UserManager()
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']

    @property
    def get_full_name(self) -> str:
        if self.first_name or self.last_name or self.middle_name:
            return f"{self.first_name} {self.last_name} {self.middle_name}"

    def __str__(self) -> str:
        return f"{self.phone}"





class ResetPasword(TimeStampAbstractModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='codes',
    )
    is_active = models.BooleanField()
    code = models.IntegerField(
        unique=True,
        default=generate_code
    )
    date = models.DateTimeField(
        auto_now_add=True,
        auto_created=True,
        blank=True,
        null=True
    )
    is_test = models.BooleanField(
        default=False,
        verbose_name="Тестовый режим"
    )

    def __str__(self) -> str:
        return f"{self.user.phone}--{self.code}"
        
    class Meta:
        verbose_name = 'Код для сброса пароля'
        verbose_name_plural = 'Коды для  сброса пароля'  
        ordering = ['-id']



class PhoneNumberChange(TimeStampAbstractModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='phone_numbers',
    )
    is_active = models.BooleanField(
        default=True
    )
    new_phone_number = PhoneNumberField(
        max_length=20,
        unique=True,
    )
    code = models.IntegerField(
        unique=True,
        default=generate_code
    )
    is_test = models.BooleanField(
        default=False,
        verbose_name="Тестовый режим"
    )

    class Meta:
        verbose_name = 'Код для изменение номер телефона'
        verbose_name_plural = 'Коды для изменение номер телефона'
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.get_full_name}-{self.new_phone_number}-{self.code}"    
    


