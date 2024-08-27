from celery import shared_task
from .main import GazeTrackingSession
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def process_gaze_tracking(user_id, interview_id, local_video_path):
    try:
        gaze_session_key = f"{user_id}_{interview_id}"
        gaze_session = GazeTrackingSession(video_url=local_video_path, status="initialized")
        gaze_session.start_eye_tracking(local_video_path)

        # 세션 종료 후, 결과를 저장하거나 추가 작업 수행
        logger.info(f"Gaze tracking completed for session {gaze_session_key}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error during gaze tracking: {e}")
        return {"status": "error", "message": str(e)}
