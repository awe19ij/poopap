from django.shortcuts import render

# Create your views here.
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from InterviewAnalyze.models import InterviewAnalysis, voiceAnalysis, QuestionLists
from django.contrib.auth.models import User
from Eyetrack.models import GazeTrackingResult, Video


class MyInterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, interview_id):
        if request.user.id != user_id:
            return Response({"error": "You are not authorized to view this interview."}, status=403)

        try:
            interview = InterviewAnalysis.objects.get(id=interview_id, user_id=user_id)
        except InterviewAnalysis.DoesNotExist:
            raise Http404("No InterviewAnalysis found matching the criteria.")


        response_data = {
            "id": interview.id,
            "question_list_id": interview.question_list.id,
            "responses": [{
                "response": getattr(interview, f'response_{i}', ''),
                "redundancies": getattr(interview, f'redundancies_{i}', ''),
                "inappropriateness": getattr(interview, f'inappropriateness_{i}', ''),
                "corrections": getattr(interview, f'corrections_{i}', ''),
                "corrected_response": getattr(interview, f'corrected_response_{i}', '')
            } for i in range(1, 11)],
            "overall_feedback": interview.overall_feedback,
            "created_at": interview.created_at
        }

        return Response(response_data, status=200)


class MyInterviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id != user_id:
            return Response({"error": "You are not authorized to view these interviews."}, status=403)

        interviews = InterviewAnalysis.objects.filter(user_id=user_id).order_by('-created_at')
        response_data = [{
            "id": interview.id,
            "created_at": interview.created_at
        } for interview in interviews]

        return Response(response_data, status=200)

class GazeTrackingResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, interview_id):
        if request.user.id != user_id:
            return Response({"error": "You are not authorized to view this gaze tracking result."}, status=403)

        gaze_tracking_results = GazeTrackingResult.objects.filter(user_id=user_id, interview_id=interview_id)
        if not gaze_tracking_results:
            return Response({"error": "No GazeTrackingResult found matching the criteria."}, status=404)

        # 여러 결과 처리를 위해 리스트를 반환하거나 첫 번째 결과만 선택
        # 예: 첫 번째 결과 반환
        gaze_tracking_result = gaze_tracking_results.first()
        video = Video.objects.filter(user_id=user_id, interview_id=interview_id).first()
        video_url = video.file.url if video else None

        response_data = {
            "id": interview_id,
            "image_data": gaze_tracking_result.encoded_image,
            "feedback": gaze_tracking_result.feedback,
            "video_url": video_url
        }

        return Response(response_data, status=200)

    

# 이서코드
class AnalysisResultListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, interview_id):
        if request.user.id != user_id:
            return Response({"error": "You are not authorized to view this interview."}, status=403)

        try:
            interview = voiceAnalysis.objects.get(id=interview_id, user_id=user_id)
        except InterviewAnalysis.DoesNotExist:
            raise Http404("No voiceAnalysis found matching the criteria.")

        response_data = {
            "id": interview.id,
            "question_list_id": interview.question_list.id,
            "pitch_graph": interview.pitch_graph,
            "intensity_graph": interview.intensity_graph,
            "pitch_summary": interview.pitch_summary,
            "intensity_summary": interview.intensity_summary,
            "created_at": interview.created_at,
        }

        return Response(response_data, status=200)
