from django.urls import path
from .views import RegisterView, LoginView, ProductView, CartView, LogoutView, CartItemDeleteView, ProductDeleteView, \
     MyOrdersView, OrderItems

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/',LogoutView.as_view()),
    path('products/', ProductView.as_view()),
    path('cart/', CartView.as_view()),
    path('remove-cart/', CartItemDeleteView.as_view()),
    path('delete-product/', ProductDeleteView.as_view()),
    path('place-order/', OrderItems.as_view()),
    path('my-orders/', MyOrdersView.as_view()),
]