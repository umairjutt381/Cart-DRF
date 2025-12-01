from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class UsernameEmailPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()

        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        if user is None:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                pass
        if user is None:
            try:
                user = User.objects.get(phone=username)
            except User.DoesNotExist:
                pass
        if user is None:
            return None

        if user.check_password(password):
            return user
        return None