from django.urls import path
from .views import *

urlpatterns = [
    path('responses/<int:user_id>/<int:interview_id>/', ResponseAPIView.as_view(), name='interview_responses'),
    path('voice/<int:user_id>/<int:question_id>/', VoiceAPIView.as_view(), name='voice'), 
 
]
 