from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from .models import RegUser
from .serializers import RegUserDeepSerializer
# Create your views here.


class RegUserViewSet(viewsets.ModelViewSet):
    queryset = RegUser.objects.all()
    serializer_class = RegUserDeepSerializer
    http_method_names = ('options', 'get', 'post',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'id': serializer.instance.pk})
        return Response({'success': False, 'errors': serializer.errors}, status=400)
