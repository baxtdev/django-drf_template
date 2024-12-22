from django.contrib.auth.models import UserManager as BaseUserManager
from django.db.models import Case, When, BooleanField
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_queryset(self):
        now = timezone.now()
        online_time = now - timezone.timedelta(minutes=5)

        return super().get_queryset().select_related(
            'auth_token',
        ).annotate(
            online=Case(
                When(last_activity__gt=online_time, then=True),
                default=False, output_field=BooleanField()
            ),
        )
    
    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError('Phone must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone, password, **extra_fields)