from django.http import HttpRequest
from ninja_extra.throttling import SimpleRateThrottle


class _IPRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request: HttpRequest):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginRateThrottle(_IPRateThrottle):
    scope = "login"


class RegisterRateThrottle(_IPRateThrottle):
    scope = "register"


class PasswordResetThrottle(_IPRateThrottle):
    scope = "password_reset"
