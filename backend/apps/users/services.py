"""
Users services - regras de negócio de usuário fora das views.
"""
from django.contrib.auth import get_user_model

User = get_user_model()


class UserService:
    @staticmethod
    def create_user(*, name, email, password, role):
        """Cria um usuário aplicando normalização de email."""
        return User.objects.create_user(
            name=name,
            email=email.strip().lower(),
            password=password,
            role=role,
        )

    @staticmethod
    def set_password(user, new_password):
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
        return user

    @staticmethod
    def deactivate(user):
        """Desativa (soft delete) em vez de apagar, para preservar histórico/auditoria."""
        user.is_active = False
        user.save(update_fields=['is_active', 'updated_at'])
        return user
