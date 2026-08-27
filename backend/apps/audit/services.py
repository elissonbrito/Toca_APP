"""
Audit service - registro centralizado de ações.
"""


def client_ip(request):
    """Extrai o IP do cliente respeitando proxy reverso."""
    if request is None:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AuditService:
    @staticmethod
    def log(user, action: str, entity: str, entity_id=None, details: str = '',
            ip_address=None, request=None):
        """Cria uma entrada de auditoria. Nunca deixa o fluxo principal quebrar.

        Se ``request`` for passado, o IP e (quando ``user`` for None) o usuário
        autenticado são extraídos dele.
        """
        try:
            from .models import AuditLog

            if request is not None:
                if ip_address is None:
                    ip_address = client_ip(request)
                if user is None and getattr(request, 'user', None) and request.user.is_authenticated:
                    user = request.user

            AuditLog.objects.create(
                user=user if getattr(user, 'is_authenticated', False) else None,
                action=action,
                entity=entity,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
            )
        except Exception:
            # Auditoria nunca derruba a operação de negócio.
            pass
