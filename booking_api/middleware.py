from django.utils import timezone
from pytz import timezone as pytz_timezone 

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.headers.get('X-Timezone', 'Asia/Kolkata')
        try:
            timezone.activate(pytz_timezone(tzname))
        except Exception:
            print(f"Invalid timezone: {tzname}. Defaulting to 'Asia/Kolkata'.")
            timezone.activate(pytz_timezone('Asia/Kolkata'))
        
        return self.get_response(request)
