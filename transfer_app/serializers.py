from django.contrib.auth.models import User

from rest_framework import serializers

from transfer_app.models import Resource, Transfer, TransferCoordinator


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class ResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resource
        fields = ('id', \
                  'source', \
                  'path', \
                  'size', \
                  'owner', \
                  'is_active', \
                  'date_added', \
                  'expiration_date' \
        )


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ('id', \
                  'resource', \
                  'download', \
                  'destination', \
                  'completed', \
                  'success', \
                  'start_time', \
                  'finish_time', \
                  'coordinator',
        )

class TransferCoordinatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferCoordinator
        fields = ('id', 'completed')

