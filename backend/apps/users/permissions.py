"""
Users app permissions.
"""
from rest_framework.permissions import BasePermission
from .models import UserRole


class IsAdminMaximo(BasePermission):
    """Only ADM_MAXIMO can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.ADM_MAXIMO


class IsManager(BasePermission):
    """ADM_MAXIMO or GERENTE can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsKitchenStaff(BasePermission):
    """Kitchen staff access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.COZINHA, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsParrillaStaff(BasePermission):
    """Parrilla staff access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.PARRILLA, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsKitchenOrParrilla(BasePermission):
    """Cozinha ou parrilla (painel de preparo compartilhado, filtrado por setor)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.COZINHA, UserRole.PARRILLA, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsCaixa(BasePermission):
    """Caixa access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.CAIXA, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsGarcom(BasePermission):
    """Garçom access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.GARCOM, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsFloorStaff(BasePermission):
    """Quem opera o salão: garçom, recepção, gerente, admin (pode abrir comandas)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.GARCOM, UserRole.RECEPCAO, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]


class IsFloorStaffOrCaixa(BasePermission):
    """Salão + caixa: fechar conta pode ser feito pelo garçom ou pelo caixa."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.GARCOM, UserRole.RECEPCAO, UserRole.CAIXA,
            UserRole.ADM_MAXIMO, UserRole.GERENTE,
        ]


class IsCaixaOrAdmin(BasePermission):
    """Somente Caixa e Administrador Máximo — troca de mesa e transferência de itens.

    Não inclui a gerência de propósito: é uma ação sensível (mexe na conta do
    cliente) reservada a quem opera o caixa e ao ADM.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.CAIXA, UserRole.ADM_MAXIMO,
        ]


class IsRecepcao(BasePermission):
    """Recepção access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.RECEPCAO, UserRole.ADM_MAXIMO, UserRole.GERENTE
        ]
