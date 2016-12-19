
from django.shortcuts import get_object_or_404, reverse
from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sendfile import sendfile

from .exceptions import PasswordNotMatching
from .models import Profile, RegUser, User
from .permissions import IsUserSelf, IsRegisteringOrSelf
from .serializers import PasswordChangeSerializer, RegUserDeepSerializer, SecurityQuestionSerializer

import logging


logger = logging.getLogger('dooit.users.views')


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
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response['Location'] = request.build_absolute_uri(reverse('api:profile-image', kwargs={'user_pk': user.pk}))
        return response

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

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def change_security_question(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            logger.log(logging.DEBUG, 'Security question change not authorised.')
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        logger.log(logging.DEBUG, 'Security question change authorised.')
        serializer = SecurityQuestionSerializer(data=request.data, context=self.get_serializer_context())
        if serializer.is_valid(raise_exception=True):
            user = request.user
            data = request.data
            user.profile.set_security_question(data.get('new_question'), data.get('new_answer'))
            user.profile.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get', 'post'])
    def verify_security_question(self, request, pk=None, *args, **kwargs):
        if request.method == 'GET':
            user = get_object_or_404(User, pk=pk)
            return Response(data=user.profile.security_question, status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'POST':
            user = get_object_or_404(User, pk=pk)
            data = request.data
            answer = data.get('answer')
            if user.profile.verify_security_question(answer):
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SecurityQuestionView(GenericAPIView):
    """View to get and verify security question."""
    queryset = Profile.objects.all()

    def get(self, request, *args, **kwarg):
        logger.log(logging.DEBUG, 'Getting security question')
        username = request.query_params.get('username', None)
        if username is None:
            return Response(
                data={
                    'field_errors': {
                        'username': [_('Required.')]}},
                status=status.HTTP_400_BAD_REQUEST)

        logger.log(logging.DEBUG, 'Username: ' + (username if username else 'NULL'))
        try:
            profile = self.get_queryset().get(user__username=username)
        except Profile.DoesNotExist:
            return Response(
                data={
                    'field_errors': {
                        'username': [_('No such username exists.')]}},
                status=status.HTTP_404_NOT_FOUND)

        logger.log(logging.DEBUG, 'Profile fetched')
        return Response(data=profile.security_question)

    def post(self, request, *args, **kwarg):
        valid = True
        errors = {'field_errors': {}}
        data = request.data

        username = request.query_params.get('username', None) or data.get('username', None)
        if not username:
            valid = False
            profile = None
            errors['field_errors']['username'] = [_('Required.')]
        else:
            try:
                profile = get_object_or_404(self.get_queryset(), user__username=username)
            except Profile.DoesNotExist:
                valid = False
                profile = None
                errors['field_errors']['username'] = [_('No such username exists.')]
            except:
                valid = False
                profile = None
                errors['field_errors']['username'] = [_('Unknown username error.')]

        answer = data.get('answer', None)
        if not answer:
            valid = False
            errors['field_errors']['answer'] = [_('Required.')]
        elif profile and not profile.verify_security_question(answer):
            valid = False
            errors['field_errors']['answer'] = [_('Incorrect answer (remember capital letters).')]

        password = request.data.get('new_password', None)
        if not password:
            valid = False
            errors['field_errors']['new_password'] = [_('Required.')]

        if not valid:
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

        user = profile.user
        User.set_password(user, password)
        user.save()
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
