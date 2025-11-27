from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import *
from .models import User, Product, Cart, CartItem


class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        phone = request.data.get("phone")
        password = request.data.get("password")
        user = None
        if username:
            user = authenticate(username=username, password=password)
        elif phone:
            try:
                u = User.objects.get(phone=phone)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key
            })

        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        token = request.auth                                                   # current user's token
        if token:
            token.delete()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        return Response({"detail": "No token found."}, status=status.HTTP_400_BAD_REQUEST)


class ProductView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superusers can add products"},
                status=status.HTTP_403_FORBIDDEN
            )
        product_name = request.data.get("name")
        if not product_name:
            return Response({"error": "Product name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            products = Product.objects.filter(name=product_name)
            added_stock = int(request.data.get("stock", 0))
            for product in products:
                product.stock += added_stock
                product.save()

            return Response(
                {"message": "Product already exists. Stock updated successfully"},
                status=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "New product created successfully"},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Only admin users can delete products"},
                status=status.HTTP_403_FORBIDDEN
            )
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        product.delete()
        return Response({"message": "Product deleted successfully"}, status=200)


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity"))
        cart, _ = Cart.objects.get_or_create(user=request.user)
        try:
            product = Product.objects.get(id=product_id)              #to check product
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product,defaults={"quantity":quantity})
        if not created:
            item.quantity += quantity
        item.save()
        return Response({"message": "Product added to cart"})


class CartItemDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        product_id = request.data.get("product_id")
        remove_qty = int(request.data.get("quantity",0))
        if not product_id or remove_qty <= 0:
            return Response({"error": "Invalid product_id or quantity"}, status=400)
        cart = Cart.objects.get(user=request.user)
        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({"error": "Product not found in cart"}, status=404)
        if remove_qty > item.quantity:
            return Response(
                {"error": f"You cannot remove more than {item.quantity}"},
                status=400
            )
        item.quantity -= remove_qty
        item.save()
        return Response(
            {"message": "Product quantity reduced successfully",
             "remaining_quantity": item.quantity},
            status=200
        )


class OrderItems(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=404)
        if not cart.items.exists():
            return Response({"error": "Your cart is empty"}, status=400)
        payment_method = request.data.get("payment_method", "cash")
        order = Order.objects.create(user=request.user, payment_method=payment_method)
        total = 0
        for item in cart.items.all():
            product = item.product
            if item.quantity > product.stock:
                return Response(
                    {"error": f"Not enough stock for {product.name}. Available: {product.stock}"},
                    status=400
                )
            total_price = product.price * item.quantity
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                total_price=total_price
            )
            product.stock -= item.quantity
            product.save()
            item.delete()
            total += total_price
        order.total_amount = total
        order.save()
        return Response({
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_amount": total
        }, status=201)

class MyOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        data = []
        for order in orders:
            items = order.items.all()
            items_data = [
                {
                    "product": i.product.name,
                    "quantity": i.quantity,
                    "total_price": i.total_price
                } for i in items
            ]

            data.append({
                "order_id": order.id,
                "total_amount": order.total_amount,
                "payment_method": order.payment_method,
                "items": items_data,
                "created_at": order.created_at
            })
        return Response(data)
