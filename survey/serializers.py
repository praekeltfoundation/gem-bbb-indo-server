
from rest_framework.serializers import ModelSerializer

from .models import CoachSurvey, CoachFormField


class CoachSurveyFieldSerializer(ModelSerializer):

    class Meta:
        model = CoachFormField
        fields = '__all__'


class CoachSurveySerializer(ModelSerializer):
    custom_form_fields = CoachSurveyFieldSerializer(many=True)

    class Meta:
        model = CoachSurvey
        fields = '__all__'
