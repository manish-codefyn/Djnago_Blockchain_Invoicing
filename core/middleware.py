from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.urls import resolve
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Add security headers to all responses
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP Header - adjust based on your needs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
        )
        response['Content-Security-Policy'] = csp
        
        return response

class EncryptionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Decrypt any encrypted fields in POST data
        if request.method == 'POST':
            try:
                cipher_suite = Fernet(settings.ENCRYPTION_KEY)
                for key, value in request.POST.items():
                    if key.startswith('enc_'):
                        try:
                            decrypted_value = cipher_suite.decrypt(value.encode()).decode()
                            request.POST = request.POST.copy()
                            request.POST[key[4:]] = decrypted_value
                        except InvalidToken:
                            logger.warning(f"Failed to decrypt field {key}")
                            continue
            except Exception as e:
                logger.error(f"Error in EncryptionMiddleware: {e}")

    def process_response(self, request, response):
        # Encrypt sensitive data in responses if needed
        if hasattr(response, 'data') and isinstance(response.data, dict):
            try:
                cipher_suite = Fernet(settings.ENCRYPTION_KEY)
                for key in ['payment_details', 'credit_card', 'bank_account']:
                    if key in response.data:
                        encrypted_value = cipher_suite.encrypt(str(response.data[key]).encode()).decode()
                        response.data[key] = f"enc_{encrypted_value}"
            except Exception as e:
                logger.error(f"Error encrypting response data: {e}")
        return response