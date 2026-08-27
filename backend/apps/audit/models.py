from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Usuário'
    )
    action = models.CharField('Ação', max_length=20)
    entity = models.CharField('Entidade', max_length=50)
    entity_id = models.PositiveIntegerField('ID da Entidade', null=True, blank=True)
    details = models.TextField('Detalhes', blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} - {self.entity} #{self.entity_id} por {self.user}'
