from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from api.serializers import UserSerializer, ApartmentSerializer
from api.permissions import IsAdminRole, IsOwnerOrReadOnly
from api.models import Apartment, UserConfig

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class LoginView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            return Response(data = {
                "token": jwt_encode_handler(jwt_payload_handler(user)),
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "email": user.email,
                    "role": user.config.role
                },
            })

        return Response(status=status.HTTP_400_BAD_REQUEST)

class SignupView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    model = User
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    queryset = User.objects.all()

class ApartmentViewSet(viewsets.ModelViewSet):
    model = Apartment
    serializer_class = ApartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Apartment.objects.all()

    def perform_create(self, serializer):
        realtor_id = self.request.data.get('realtor', None)
        if realtor_id is not None:
            realtor = User.get(id=realtor_id)
        else:
            realtor = self.request.user

        if realtor.config.role != UserConfig.USER_ROLE_REALTOR:
            return Response(data={
                "detail": "A user should be realtor"
            }, status=status.HTTP_400_BAD_REQUEST)

        apartment = serializer.save(realtor=realtor)
        apartment.save()
