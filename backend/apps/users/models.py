"""
Users app models - Custom User model with role-based access control.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class UserRole(models.TextChoices):
    ADM_MAXIMO = 'ADM_MAXIMO', 'Administrador Máximo'
    GERENTE = 'GERENTE', 'Gerente'
    GARCOM = 'GARCOM', 'Garçom'
    COZINHA = 'COZINHA', 'Cozinha'
    PARRILLA = 'PARRILLA', 'Parrilla'
    CAIXA = 'CAIXA', 'Caixa'
    RECEPCAO = 'RECEPCAO', 'Recepção'


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access control."""
    name = models.CharField('Nome', max_length=150)
    email = models.EmailField('Email', unique=True)
    role = models.CharField(
        'Perfil',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.GARCOM
    )
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Staff', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.role})'

    @property
    def is_admin(self):
        return self.role == UserRole.ADM_MAXIMO

    @property
    def is_manager(self):
        return self.role in [UserRole.ADM_MAXIMO, UserRole.GERENTE]
