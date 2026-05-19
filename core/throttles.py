from ninja_extra.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"


class RegisterRateThrottle(SimpleRateThrottle):
    scope = "register"


class PasswordResetThrottle(SimpleRateThrottle):
    scope = "password_reset"
