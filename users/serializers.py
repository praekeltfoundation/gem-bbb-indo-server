from rest_framework import serializers
from .models import Profile, RegUser


class RegUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = RegUser


class RegUserProfileSerializer(serializers.ModelSerializer):
    user = RegUserSerializer()

    class Meta:
        model = Profile
        depth = 1

    def __init__(self, *args, **kwargs):
        super(RegUserProfileSerializer, self).__init__(*args, **kwargs)
        if hasattr(self, 'initial_data'):
            data = self.initial_data
            user = data.get('user')
            if user is not None:
                if user.get('username') is None and data.get('mobile') is not None:
                    user['username'] = data.get('mobile')

    def validate_mobile(self, value):
        return Profile.mobile_regex(value)

    def create(self, validated_data):
        profile_data = validated_data
        user_data = validated_data.pop('user')
        user = RegUser.objects.create(**user_data)
        profile = Profile.objects.create(user=user, **profile_data)
        return profile
