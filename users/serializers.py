from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Profile, RegUser


class RegUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = RegUser
        exclude = ('profile',)


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


class ProfileSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()

    def get_profile_image_url(self, obj):
        if not obj.profile_image:
            return None
        request = self.context.get('request')
        return reverse('profile-image', request=request, kwargs={'user_pk': obj.user.pk})

    class Meta:
        model = Profile
        exclude = ('id', 'user', 'profile_image')


class RegUserDeepSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = RegUser
        depth = 1
        fields = ('id', 'username', 'password', 'profile', 'email')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def __init__(self, *args, **kwargs):
        super(RegUserDeepSerializer, self).__init__(*args, **kwargs)
        if hasattr(self, 'initial_data'):
            data = self.initial_data
            profile = data.get('profile')
            if profile is not None:
                if data.get('username') is None and profile.get('mobile') is not None:
                    data['username'] = profile.get('mobile')

    def create(self, validated_data):
        user_data = validated_data
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')
        user = RegUser.objects.create(**user_data)
        # Required to hash password
        user.set_password(password)
        user.save()
        profile = Profile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        # TODO: Do not allow password to be updated via RegUserDeepSerializer
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super(RegUserDeepSerializer, self).update(instance, validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    class Meta:
        fields = '__all__'
        extra_kwargs = {
            'old_password': {'write_only': True},
            'new_password': {'write_only': True}
        }
