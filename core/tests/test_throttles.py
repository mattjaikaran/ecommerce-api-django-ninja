from core.throttles import LoginRateThrottle, PasswordResetThrottle, RegisterRateThrottle


class TestThrottleClasses:
    def test_login_throttle_scope(self):
        assert LoginRateThrottle.scope == "login"

    def test_register_throttle_scope(self):
        assert RegisterRateThrottle.scope == "register"

    def test_password_reset_throttle_scope(self):
        assert PasswordResetThrottle.scope == "password_reset"

    def test_login_throttle_is_simple_rate_throttle(self):
        from ninja_extra.throttling import SimpleRateThrottle

        assert issubclass(LoginRateThrottle, SimpleRateThrottle)

    def test_register_throttle_is_simple_rate_throttle(self):
        from ninja_extra.throttling import SimpleRateThrottle

        assert issubclass(RegisterRateThrottle, SimpleRateThrottle)

    def test_password_reset_throttle_is_simple_rate_throttle(self):
        from ninja_extra.throttling import SimpleRateThrottle

        assert issubclass(PasswordResetThrottle, SimpleRateThrottle)
