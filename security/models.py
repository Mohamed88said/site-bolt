from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import secrets
import pyotp

User = get_user_model()

class TwoFactorAuth(models.Model):
    """Authentification à deux facteurs"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    secret_key = models.CharField(max_length=32, verbose_name=_('Clé secrète'))
    backup_codes = models.JSONField(default=list, verbose_name=_('Codes de secours'))
    is_enabled = models.BooleanField(default=False, verbose_name=_('Activé'))
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Authentification 2FA')
        verbose_name_plural = _('Authentifications 2FA')
    
    def __str__(self):
        return f"2FA {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = pyotp.random_base32()
        if not self.backup_codes:
            self.backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        super().save(*args, **kwargs)
    
    def get_qr_code_url(self):
        """Générer l'URL du QR code pour l'authentificateur"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=self.user.email,
            issuer_name="E-Commerce Guinée"
        )
    
    def verify_token(self, token):
        """Vérifier un token TOTP"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)
    
    def verify_backup_code(self, code):
        """Vérifier un code de secours"""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            self.save()
            return True
        return False

class SecurityLog(models.Model):
    """Journal de sécurité"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    action = models.CharField(max_length=50, verbose_name=_('Action'))
    ip_address = models.GenericIPAddressField(verbose_name=_('Adresse IP'))
    user_agent = models.TextField(blank=True, verbose_name=_('User Agent'))
    location_data = models.JSONField(default=dict, verbose_name=_('Données de localisation'))
    success = models.BooleanField(default=True, verbose_name=_('Succès'))
    details = models.JSONField(default=dict, verbose_name=_('Détails'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Log de sécurité')
        verbose_name_plural = _('Logs de sécurité')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"

class DataEncryption(models.Model):
    """Chiffrement des données sensibles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data_type = models.CharField(max_length=50, verbose_name=_('Type de données'))
    encrypted_data = models.TextField(verbose_name=_('Données chiffrées'))
    encryption_key_id = models.CharField(max_length=100, verbose_name=_('ID clé de chiffrement'))
    created_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Données chiffrées')
        verbose_name_plural = _('Données chiffrées')

class AuditTrail(models.Model):
    """Piste d'audit complète"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100, verbose_name=_('Action'))
    model_name = models.CharField(max_length=50, verbose_name=_('Modèle'))
    object_id = models.CharField(max_length=100, verbose_name=_('ID objet'))
    old_values = models.JSONField(default=dict, verbose_name=_('Anciennes valeurs'))
    new_values = models.JSONField(default=dict, verbose_name=_('Nouvelles valeurs'))
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Piste d\'audit')
        verbose_name_plural = _('Pistes d\'audit')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.model_name}"