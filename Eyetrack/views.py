from django.shortcuts import render
from django.http import JsonResponse
from .main import GazeTrackingSession
from .models import GazeTrackingResult, Video
import cv2
import pandas as pd
import base64
import io
from PIL import Image
import numpy as np
import os
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import VideoSerializer, SignedURLSerializer, GazeStatusSerializer
from django.conf import settings
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
import datetime
import requests
from django.shortcuts import get_object_or_404
from django.core.exceptions import MultipleObjectsReturned
from .models import GazeTrackingResult, Video
from .tasks import process_gaze_tracking


logger = logging.getLogger(__name__)
permission_classes = [IsAuthenticated]
gaze_sessions = {}

def generate_signed_url(bucket_name, blob_name, expiration=86400):
    client = storage.Client()
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(
            expiration=datetime.timedelta(seconds=expiration),
            method='PUT'
        )
        return url
    except GoogleCloudError as e:
        raise ValueError(f"서명된 URL 생성 실패: {e}")
    except Exception as e:
        raise ValueError(f"서명된 URL 생성 중 예기치 않은 오류 발생: {e}")


class SignedURLView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, user_id, interview_id, *args, **kwargs):
        serializer = SignedURLSerializer(data=request.data)
        if serializer.is_valid():
            bucket_name = settings.GS_BUCKET_NAME
            blob_name = f"videos/{user_id}/{interview_id}/input.webm"
            try:
                signed_url = generate_signed_url(bucket_name, blob_name)
                key = f"{user_id}_{interview_id}"
                if key not in gaze_sessions:
                    gaze_sessions[key] = GazeTrackingSession(video_url=signed_url, status="initialized")
                return JsonResponse({"signed_url": signed_url}, status=200)
            except ValueError as e:
                return JsonResponse({"message": str(e)}, status=500)
        else:
            return JsonResponse(serializer.errors, status=400)




class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id, interview_id):
        file_url = f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/videos/{user_id}/{interview_id}/input.webm'
        video = Video.objects.create(user_id=user_id, interview_id=interview_id, file=file_url)
        return JsonResponse({'message': 'Video saved successfully', 'video_id': video.id}, status=201)


def download_video_from_public_url(video_url, local_path):
    """원격 URL에서 비디오를 다운로드하여 로컬 파일로 저장"""
    try:
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)  # 디렉토리가 없는 경우 생성
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"File downloaded successfully to {local_path}")
        else:
            error_msg = f"Failed to download file, status code: {response.status_code}. URL: {video_url}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Error downloading video from public URL: {e}")
        raise

def start_gaze_tracking_view(request, user_id, interview_id):
    key = f"{user_id}_{interview_id}"

    try:
        # 비디오 파일의 GCS URL을 생성합니다.
        video_url = f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/videos/{user_id}/{interview_id}/input.webm'

        # `media` 폴더 내에 로컬 경로 생성
        local_video_path = os.path.join(settings.BASE_DIR, 'media', f'{user_id}_{interview_id}_input.webm')

        # 원격 URL에서 로컬로 다운로드
        download_video_from_public_url(video_url, local_video_path)
    except ValueError as e:
        logger.error(f"Failed to download video: {e}")
        return JsonResponse({"message": str(e)}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error during video download: {e}")
        return JsonResponse({"message": f"Unexpected error during video download: {str(e)}"}, status=500)

    try:
        # 세션을 `gaze_sessions`에 추가
        if key not in gaze_sessions:
            gaze_sessions[key] = GazeTrackingSession(video_url=video_url, status="initialized")
        else:
            logger.warning(f"Session already exists for user_id={user_id} and interview_id={interview_id}")

        # Celery 작업으로 시선 추적 분석을 비동기적으로 실행
        process_gaze_tracking.delay(user_id, interview_id, local_video_path)
        return JsonResponse({"message": "Gaze tracking started, processing in background"}, status=200)
    except Exception as e:
        logger.error(f"Error initiating gaze tracking: {e}")
        return JsonResponse({"message": f"Error initiating gaze tracking: {str(e)}"}, status=500)


def apply_gradient(center, radius, color, image, text=None):
    overlay = image.copy()
    cv2.circle(overlay, center, radius, color, -1)
    cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        font_color = (255, 255, 255)
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = center[0] - text_size[0] // 2
        text_y = center[1] + text_size[1] // 2
        cv2.putText(image, text, (text_x, text_y), font, font_scale, font_color, thickness)

def assign_colors_and_numbers(section_counts):
    colors = [
        (38, 38, 255), (59, 94, 255), (55, 134, 255),
        (51, 173, 255), (26, 210, 255), (0, 255, 255)
    ]
    sorted_sections = sorted(section_counts.items(), key=lambda item: item[1], reverse=True)
    color_map = {}
    number_map = {}
    for i, (section, _) in enumerate(sorted_sections):
        color_map[section] = colors[i % len(colors)]
        number_map[section] = str(i + 1)
    return color_map, number_map

def draw_heatmap(image, section_counts):
    height, width, _ = image.shape
    section_centers = {
        "A": (int(width / 6), int(height / 2)),
        "B": (int(width / 2), int(height / 2)),
        "C": (int(5 * width / 6), int(height / 2))
    }
    color_map, number_map = assign_colors_and_numbers(section_counts)
    for section, count in section_counts.items():
        if count > 0 and section in section_centers:
            center = section_centers[section]
            color = color_map[section]
            number = number_map[section]
            radius = int(width / 12)  # Dynamic radius based on image width
            apply_gradient(center, radius, color, image, number)


# # 히트맵 png 스토리지 업로드
# def upload_image_to_gcs(bucket_name, blob_name, image_content):
#     client = storage.Client()
#     bucket = client.bucket(bucket_name)
#     blob = bucket.blob(blob_name)

#     blob.upload_from_string(image_content, content_type='image/png')
#     # 공개 액세스를 위해 파일을 공개 설정
#     blob.make_public()
#     return blob.public_url

# 이미지 스토리지 업로드 아닌 버전
def stop_gaze_tracking_view(request, user_id, interview_id):
    key = f"{user_id}_{interview_id}"
    if key not in gaze_sessions:
        return JsonResponse({"message": "Session not found", "status": "error"}, status=404)

    gaze_session = gaze_sessions[key]
    csv_filename = gaze_session.stop_eye_tracking()
    section_data = pd.read_csv(csv_filename)
    section_counts = dict(zip(section_data["Section"], section_data["Count"]))
    image_path = os.path.join(settings.BASE_DIR, "Eyetrack", "0518", "image.png")
    original_image = cv2.imread(image_path)
    if original_image is None:
        return JsonResponse({"message": "Image not found", "status": "error"}, status=404)

    heatmap_image = original_image.copy()
    draw_heatmap(heatmap_image, section_counts)
    _, buffer = cv2.imencode('.png', heatmap_image)
    encoded_image_data = "data:image/png;base64," + base64.b64encode(buffer).decode('utf-8')
    feedback = get_feedback(section_counts)

    video = Video.objects.filter(user_id=user_id, interview_id=interview_id).first()
    video_url = video.file.url if video else None

    gaze_tracking_result = GazeTrackingResult.objects.create(
        user_id=user_id,
        interview_id=interview_id,
        encoded_image=encoded_image_data,
        feedback=feedback
    )

    local_video_path = os.path.join(settings.MEDIA_ROOT, f"{user_id}_{interview_id}.webm")
    if os.path.exists(local_video_path):
        os.remove(local_video_path)
    del gaze_sessions[key]

    return JsonResponse({
        "message": "Gaze tracking stopped",
        "image_data": gaze_tracking_result.encoded_image,
        "video_url": video_url,
        "feedback": feedback,
        "status": "success"
    }, status=200)

# def stop_gaze_tracking_view(request, user_id, interview_id):
#     key = f"{user_id}_{interview_id}"
#     if key not in gaze_sessions:
#         return JsonResponse({"message": "Session not found", "status": "error"}, status=404)

#     gaze_session = gaze_sessions[key]
#     csv_filename = gaze_session.stop_eye_tracking()
#     section_data = pd.read_csv(csv_filename)
#     section_counts = dict(zip(section_data["Section"], section_data["Count"]))
#     image_path = os.path.join(settings.BASE_DIR, "Eyetrack", "0518", "image.png")
#     original_image = cv2.imread(image_path)
#     if original_image is None:
#         return JsonResponse({"message": "Image not found", "status": "error"}, status=404)

#     heatmap_image = original_image.copy()
#     draw_heatmap(heatmap_image, section_counts)
#     _, buffer = cv2.imencode('.png', heatmap_image)
#     encoded_image_data = buffer.tobytes()

#     # 이미지를 GCS에 업로드하고 공개 URL 받기
#     bucket_name = settings.GS_BUCKET_NAME
#     blob_name = f"results/{user_id}/{interview_id}/heatmap.png"
#     image_url = upload_image_to_gcs(bucket_name, blob_name, encoded_image_data)

#     feedback = get_feedback(section_counts)
#     video = Video.objects.filter(user_id=user_id, interview_id=interview_id).first()
#     video_url = video.file.url if video else None

#     gaze_tracking_result = GazeTrackingResult.objects.create(
#         user_id=user_id,
#         interview_id=interview_id,
#         encoded_image=image_url,  # 이제 URL을 저장
#         feedback=feedback
#     )

#     local_video_path = os.path.join(settings.MEDIA_ROOT, f"{user_id}_{interview_id}.webm")
#     if os.path.exists(local_video_path):
#         os.remove(local_video_path)
#     del gaze_sessions[key]

#     return JsonResponse({
#         "message": "Gaze tracking stopped",
#         "image_url": image_url,  # URL을 JsonResponse에 포함시킴
#         "video_url": video_url,
#         "feedback": feedback,
#         "status": "success"
#     }, status=200)




def get_feedback(section_counts):
    max_section = max(section_counts, key=section_counts.get)
    feedback = "Good focus on the interviewer!"
    if max_section == 'A':
        feedback = "You are looking too much to the left. Try to focus more on the interviewer."
    elif max_section == 'C':
        feedback = "You are looking too much to the right. Try to focus more on the interviewer."
    return feedback



