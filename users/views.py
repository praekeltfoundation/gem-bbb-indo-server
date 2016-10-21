
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import views, status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import RegUser
from .serializers import ProfileSerializer, RegUserDeepSerializer


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

    def post(self, request, user_pk):
        user = get_object_or_404(RegUser, pk=user_pk)
        user.profile.profile_image = request.FILES['file']
        user.profile.save()
        serializer = self.get_serializer(RegUser.objects.get(pk=user.pk))
        return Response(serializer.data, status.HTTP_201_CREATED)


class RegUserViewSet(viewsets.ModelViewSet):
    queryset = RegUser.objects.all()
    serializer_class = RegUserDeepSerializer
    http_method_names = ('options', 'head', 'get', 'post',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'success': True, 'id': serializer.instance.pk})
