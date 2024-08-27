from rest_framework import serializers
from .models import Video

class GazeStatusSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=200)

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'file', 'uploaded_at']

# Signed URL 생성을 위한 시리얼라이저
from rest_framework import serializers

class SignedURLSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255, required=False)  # 업로드할 파일의 이름, 필수 아님
    content_type = serializers.CharField(max_length=50, required=False)  # 파일의 MIME 타입, 필수 아님

    def validate_content_type(self, value):
        # MIME 타입 검증 로직
        if value and value != 'video/webm':
            raise serializers.ValidationError("Only .webm video types are allowed.")
        return value

