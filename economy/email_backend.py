from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend

from .email_config import smtp_config


class EmailBackend(DjangoEmailBackend):
    def __init__(self, *args, **kwargs):
        config = smtp_config()
        kwargs.setdefault("host", config.get("host"))
        kwargs.setdefault("port", config.get("port"))
        kwargs.setdefault("username", config.get("username"))
        kwargs.setdefault("password", config.get("password"))
        kwargs.setdefault("use_tls", config.get("security") == "tls")
        kwargs.setdefault("use_ssl", config.get("security") == "ssl")
        super().__init__(*args, **kwargs)
