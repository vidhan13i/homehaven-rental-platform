from rest_framework.throttling import SimpleRateThrottle


class OTPRequestThrottle(SimpleRateThrottle):
    """
    Rate limiter for requesting OTPs.
    Identifies the request by email (if provided) or IP address.
    """

    scope = "otp_request"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if email:
            return self.cache_format % {
                "scope": self.scope,
                "ident": email.strip().lower(),
            }
        return self.get_ident(request)


class OTPVerifyThrottle(SimpleRateThrottle):
    """
    Rate limiter for verifying OTPs.
    Identifies the request by email (if provided) or IP address.
    """

    scope = "otp_verify"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if email:
            return self.cache_format % {
                "scope": self.scope,
                "ident": email.strip().lower(),
            }
        return self.get_ident(request)
