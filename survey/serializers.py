
from rest_framework import serializers
from rest_framework.reverse import reverse as rest_reverse

from .models import CoachSurvey, CoachFormField


class CoachSurveyFieldSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = CoachFormField
        fields = ('id', 'name', 'label', 'field_type', 'required', 'choices', 'default_value', 'help_text')

    def get_name(self, obj):
        return obj.clean_name


class CoachSurveySerializer(serializers.ModelSerializer):
    form_fields = CoachSurveyFieldSerializer(many=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = CoachSurvey
        # fields = '__all__'
        fields = ('id', 'title', 'intro', 'outro', 'url', 'form_fields')

    def get_url(self, obj):
        request = self.context['request']
        return rest_reverse('api:surveys-detail', kwargs={'pk': obj.pk}, request=request)
