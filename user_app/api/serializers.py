from rest_framework import serializers
from django.contrib.auth.models import User


class RegisterUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
    
    def save(self):
        
        if self.validated_data['password'] != self.validated_data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        if User.objects.filter(email=self.validated_data['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        if not self.validated_data['username']: 
            raise serializers.ValidationError({"username": "Username cannot be empty"})
        validated_data = self.validated_data.copy()
        del validated_data['password2']
        user = self.create(validated_data=self.validated_data)
        return user
    