from rest_framework.throttling import ScopedRateThrottle


class ForgotPasswordRateThrottle(ScopedRateThrottle):
    scope = "forgot_password"
