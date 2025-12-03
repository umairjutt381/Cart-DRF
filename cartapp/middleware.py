from django.utils.deprecation import MiddlewareMixin
import time

class SimpleLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        print("Request Path:", request.path)
        request.start_time = time.time()

    def process_response(self, request, response):
        time_taken = time.time() - request.start_time
        token = request.session.get('token')
        print("Token:", token)
        print("Time Taken:", time_taken)
        return response
