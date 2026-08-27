"""
Users app views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import User
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, ChangePasswordSerializer
from .permissions import IsAdminMaximo, IsManager
from apps.audit.services import AuditService


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""
    queryset = User.objects.all().order_by('name')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['name', 'email']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsManager()]
        return [IsAdminMaximo()]

    def perform_create(self, serializer):
        user = serializer.save()
        AuditService.log(
            user=self.request.user,
            action='CREATE',
            entity='User',
            entity_id=user.id,
            details=f'Usuário {user.name} ({user.email}) criado com perfil {user.role}'
        )

    def perform_update(self, serializer):
        user = serializer.save()
        AuditService.log(
            user=self.request.user,
            action='UPDATE',
            entity='User',
            entity_id=user.id,
            details=f'Usuário {user.name} atualizado'
        )

    def perform_destroy(self, instance):
        AuditService.log(
            user=self.request.user,
            action='DELETE',
            entity='User',
            entity_id=instance.id,
            details=f'Usuário {instance.name} desativado'
        )
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminMaximo])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': 'Senha atual incorreta.'}, status=400)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Senha alterada com sucesso.'})
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
