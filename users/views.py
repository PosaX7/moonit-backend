from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User

@api_view(["POST"])
@permission_classes([AllowAny])  # ✅ rendre l'accès public
def register(request):
    username = request.data.get("username")
    email = request.data.get("email")  # ✅ ajout du champ email
    password = request.data.get("password")

    if not username or not password:
        return Response({"detail": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    return Response({"detail": "User created successfully"}, status=status.HTTP_201_CREATED)
