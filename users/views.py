
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import detail_route
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sendfile import sendfile

from .exceptions import PasswordNotMatching
from .models import RegUser, User
from .permissions import IsUserSelf, IsRegisteringOrSelf
from .serializers import RegUserDeepSerializer, PasswordChangeSerializer


class ProfileImageView(GenericAPIView):
    parser_classes = (FileUploadParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = RegUserDeepSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }
        return self.serializer_class(*args, **kwargs)

    def check_object_permissions(self, request, obj):
        if not IsUserSelf().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only upload their own profile images.")

    def post(self, request, user_pk):
        user = get_object_or_404(User, pk=user_pk)
        self.check_object_permissions(request, user)
        user.profile.profile_image = request.FILES['file']
        user.profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, user_pk):
        user = get_object_or_404(User, pk=user_pk)
        self.check_object_permissions(request, user)
        if user.profile.profile_image:
            return sendfile(request, user.profile.profile_image.path, attachment=True)
        else:
            raise NotFound('User has no profile image.')


class RegUserViewSet(viewsets.ModelViewSet):
    queryset = RegUser.objects.all()
    serializer_class = RegUserDeepSerializer
    permission_classes = (IsRegisteringOrSelf,)
    http_method_names = ('options', 'head', 'get', 'post', 'patch',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(pk=request.user.pk), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated, IsUserSelf])
    def password(self, request, pk=None, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context=self.get_serializer_context())
        if serializer.is_valid(raise_exception=True):
            if not request.user.check_password(serializer.validated_data['old_password']):
                raise PasswordNotMatching()
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ObtainUserAuthTokenView(ObtainAuthToken):
    """View to return auth token and user profile information on successful login.
    """

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': {'token': token.key},
            'user': RegUserDeepSerializer(user, context=self.get_serializer_context()).data
        })
