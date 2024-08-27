from rest_framework import serializers
from .models import InterviewAnalysis,voiceAnalysis

class InterviewResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewAnalysis
        fields = '__all__'

class VoiceAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = voiceAnalysis
        fields = '__all__'


# class SignedURLSerializer(serializers.Serializer):
#     file_name = serializers.CharField(max_length=255, required=False)  # 업로드할 파일의 이름, 필수 아님
#     content_type = serializers.CharField(max_length=50, required=False)  # 파일의 MIME 타입, 필수 아님

#     def validate_content_type(self, value):
#         # MIME 타입 검증 로직
#         if value and value != 'audio/mp3':  # MP3 파일만 허용
#             raise serializers.ValidationError("Only .mp3 audio types are allowed.")
#         return value
