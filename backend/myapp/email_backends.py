import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend


class CustomSMTPBackend(EmailBackend):
    """
    Custom SMTP backend that handles SSL certificate verification issues
    by creating an unverified SSL context for Gmail SMTP.
    """
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        # Initialize the parent class first
        super().__init__(host, port, username, password, use_tls, fail_silently, 
                        use_ssl, timeout, ssl_keyfile, ssl_certfile, **kwargs)
    
    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        occurred.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # Use getattr with default to handle missing attributes safely
        local_hostname = getattr(self, 'local_hostname', None)
        connection_params = {}
        if local_hostname:
            connection_params['local_hostname'] = local_hostname
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            ssl_context = getattr(self, 'ssl_context', None)
            if ssl_context:
                connection_params['context'] = ssl_context
            
        try:
            print(f"Connecting to {self.host}:{self.port}")
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            # TLS/SSL are mutually exclusive, so only attempt TLS over
            # non-secure connections.
            if not self.use_ssl and self.use_tls:
                print("Starting EHLO...")
                self.connection.ehlo()
                print("Starting STARTTLS with custom context...")
                # Create unverified SSL context to bypass certificate issues
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.connection.starttls(context=context)
                print("STARTTLS successful, doing second EHLO...")
                self.connection.ehlo()

            if self.username and self.password:
                print(f"Logging in as {self.username}...")
                self.connection.login(self.username, self.password)
                print("Login successful!")
                
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            if not self.fail_silently:
                raise