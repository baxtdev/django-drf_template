import django
from django.core.validators import MinValueValidator
from rest_framework import serializers,mixins
from rest_framework import status,permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.filters import SearchFilter,OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from apps.user.models import User
from apps.utils.utils import make_bool

from .permissions import IsSuperAdmin

class SwappableSerializerMixin(object):
    def get_serializer_class(self):
        try:
            return self.serializer_classes[self.request.method]
        except AttributeError:
            raise AttributeError
        
        except KeyError:
            return super(SwappableSerializerMixin, self).get_serializer_class()


class SerializersByAction:
    serializer_classes = {}

    def get_serializer_class(self):
        if self.action == 'partial_update' or self.action == 'update_partial':
            return self.serializer_classes.get('update', self.serializer_class)
        
        return self.serializer_classes.get(self.action, self.serializer_class)


class PermissionByAction:
    permission_classes_by_action = {}

    def get_permissions(self):
        permission_classes = self.permission_classes_by_action.get(self.action, None)
        if self.action == 'partial_update' or self.action == 'update_partial':
            permission_classes = self.permission_classes_by_action.get('update', None)
        if permission_classes is None:
            permission_classes = self.permission_classes

        return [permission() for permission in permission_classes]


class PermissionByMethod:
    permission_classes_by_method = {}

    def get_permissions(self):
        method = self.request.method.lower()
        permission_classes = self.permission_classes_by_method.get(method, None)
        if permission_classes is None:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]





class DetailResponse:
    """ Works only with UpdateMixin """

    detail_serializer: Serializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        detail_serializer = self.detail_serializer(instance, many=False)

        return Response(detail_serializer.data)


class DestroyModelMixin:
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except django.db.models.deletion.ProtectedError as e:
            return Response(status=status.HTTP_423_LOCKED, data={'detail': str(e)})
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class MultipleDestroyMixinSerializer(serializers.Serializer):
    ids = serializers.ListSerializer(child=serializers.IntegerField(validators=[MinValueValidator(1)]))


class MultipleDestroyMixin:
    multiple_delete_permission = permission_classes

    @permission_classes([multiple_delete_permission])
    @action(methods=['delete'], url_path='multiple-delete', detail=False)
    def multiple_delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset()
        items = queryset.filter(id__in=serializer.data['ids'])
        not_deleted_items = []
        for item in items:
            item_id = item.id
            try:
                item.delete()
            except django.db.models.deletion.ProtectedError as e:
                not_deleted_items.append(item_id)
        return Response({
            'not_deleted_items': not_deleted_items
        }, status=status.HTTP_204_NO_CONTENT if len(not_deleted_items) == 0 else status.HTTP_423_LOCKED)

    def get_serializer_class(self):
        path = self.request.path.split('/')[-2]
        if path == 'multiple-delete':
            return MultipleDestroyMixinSerializer
        return super().get_serializer_class()


class QuerySetByUserMixin:

    def get_queryset(self):
        qs = super().get_queryset()
        user: User = self.request.user
        if user.is_authenticated:
            if not user.is_superuser:
                return qs.filter(user=user)
        return qs


class MultipleDeleteMixin:
    @action(detail=False, methods=['post'],url_path='multiple-delete')
    def multiple_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'No IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(id__in=ids)
        if not queryset.exists():
            return Response({'detail': 'No objects found with the provided IDs.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = queryset.delete()
        
        return Response({'detail': f'{count} objects deleted.'}, status=status.HTTP_204_NO_CONTENT)



class PermissoinsIsAdminUser(PermissionByAction):
    permission_classes_by_action = {
        'list': [permissions.IsAuthenticated,IsSuperAdmin],
        'create': [permissions.IsAuthenticated,IsSuperAdmin],
        'destroy': [permissions.IsAuthenticated,IsSuperAdmin],
        'retrieve':[permissions.IsAuthenticated,IsSuperAdmin],
        'update':[permissions.IsAuthenticated,IsSuperAdmin]
    }



class SuperModelViewSet(MultipleDeleteMixin,PermissoinsIsAdminUser,ModelViewSet):
    filter_backends = [DjangoFilterBackend,
                       SearchFilter,OrderingFilter]
    
    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).distinct()


class UltraSupperViewSet(MultipleDeleteMixin,PermissoinsIsAdminUser,SerializersByAction,ModelViewSet):    
    filter_backends = [DjangoFilterBackend,
                       SearchFilter,OrderingFilter]
    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).distinct()
    

class SingularViewSet(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,  
                      mixins.UpdateModelMixin,
                      GenericViewSet):
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.first()
        if obj is None:
            self.permission_denied(self.request, message="Объект не найден.")
        return obj

    def create(self, request, *args, **kwargs):
        if self.get_queryset().exists():
            return Response({"detail": "Объект уже существует. Используйте PUT/PATCH для обновления."}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

                