from django.urls import path
from .views import MyInterviewDetailView, MyInterviewListView, GazeTrackingResultView, AnalysisResultListView

urlpatterns = [
    path('<int:user_id>/interviews/', MyInterviewListView.as_view(), name='my_interview_list'),
    path('<int:user_id>/<int:interview_id>/scripts/', MyInterviewDetailView.as_view(), name='my_interview_detail'),
    path('<int:user_id>/<int:interview_id>/eyetrack/', GazeTrackingResultView.as_view(), name='gaze_tracking_result_detail'),
    path('<int:user_id>/<int:interview_id>/voice/', AnalysisResultListView.as_view(), name='analysis_result_list'),
]

