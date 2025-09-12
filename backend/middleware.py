from django.utils import timezone

class PremiumMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if (
                request.user.is_premium
                and request.user.premium_until
                and request.user.premium_until < timezone.now()
            ):
                request.user.is_premium = False
                request.user.save()
        return self.get_response(request)
