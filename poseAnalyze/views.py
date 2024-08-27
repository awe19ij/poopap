from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from google.cloud import storage
from datetime import timedelta
import os
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# pose_sessions를 전역 변수로 선언하여 관리
pose_sessions = {}

# 서명된 URL을 생성하는 함수
def generate_signed_url(bucket_name, blob_name, expiration=3600):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        expiration=timedelta(seconds=expiration),
        method='PUT'
    )
    return url

# 서명된 URL을 요청하는 뷰
class GetSignedURLView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, user_id, interview_id, *args, **kwargs):
        # 설정에서 버킷 이름을 가져옵니다. 환경 변수나 Django 설정 파일에 저장해 두세요.
        bucket_name = settings.GS_BUCKET_NAME
        if not bucket_name:
            return JsonResponse({"message": "Bucket name not found in settings"}, status=500)

        # 파일 경로 설정
        blob_name = f"pose/{user_id}/{interview_id}/pose.webm"
        
        try:
            # 서명된 URL 생성
            signed_url = generate_signed_url(bucket_name, blob_name)
            
            # 세션을 생성하여 pose_sessions에 저장
            key = f"{user_id}_{interview_id}"
            if key not in pose_sessions:
                pose_sessions[key] = {
                    "video_url": signed_url,
                    "status": "initialized"
                }
                logger.info(f"Pose session created for user_id={user_id}, interview_id={interview_id}")
            else:
                logger.warning(f"Pose session already exists for user_id={user_id}, interview_id={interview_id}")

            # 생성된 URL을 JSON 형태로 반환
            return JsonResponse({"signed_url": signed_url}, status=200)
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            return JsonResponse({"message": "Failed to generate signed URL"}, status=500)
