"""
Auth services - emissão e revogação de tokens JWT, fora das views.
"""
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.services import AuditService, client_ip as _client_ip


class AuthService:
    @staticmethod
    def issue_tokens_for(user, request=None):
        """Gera o par access/refresh para o usuário e registra o login na auditoria."""
        refresh = RefreshToken.for_user(user)
        AuditService.log(
            user=user,
            action='LOGIN',
            entity='User',
            entity_id=user.id,
            details=f'Login realizado por {user.email}',
            ip_address=_client_ip(request),
        )
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    @staticmethod
    def revoke_refresh_token(refresh_token, user=None, request=None):
        """Coloca o refresh token na blacklist. Lança TokenError se inválido."""
        token = RefreshToken(refresh_token)
        token.blacklist()
        AuditService.log(
            user=user,
            action='LOGOUT',
            entity='User',
            entity_id=getattr(user, 'id', None),
            details=f'Logout realizado por {getattr(user, "email", "desconhecido")}',
            ip_address=_client_ip(request),
        )
