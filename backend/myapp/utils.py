from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
import logging

import ssl
import socket
import smtplib

logger = logging.getLogger(__name__)

def send_activation_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_link = f"http://localhost:5173/activate/{uid}/{token}"

    subject = "Aktywuj swoje konto"
    message = f"Cześć {user.username}, kliknij link aby aktywować konto:\n{activation_link}"
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Activation email sent successfully to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
        raise  # Re-raise the exception so the view can handle it

def test_smtp_connection():
    """Test SMTP connection with unverified SSL context for debugging"""
    try:
        print("Testing SMTP connection...")
        
        # Test basic socket connection
        sock = socket.create_connection(('smtp.gmail.com', 587), timeout=10)
        print("✓ Socket connection successful")
        sock.close()
        
        # Test SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)
        server.ehlo()
        print("✓ SMTP handshake successful")
        
        # Test STARTTLS with unverified context (same as custom backend)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        server.starttls(context=context)
        print("✓ STARTTLS successful with unverified context")
        
        # Test login
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✓ Login successful")
        
        server.quit()
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False