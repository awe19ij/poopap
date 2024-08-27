from django.db import models
from QuestionList.models import QuestionLists
from django.conf import settings

class InterviewAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question_list = models.ForeignKey(QuestionLists, on_delete=models.CASCADE, null=True)  # QuestionLists 모델 참조

    response_1 = models.TextField(blank=True, null=True)
    redundancies_1 = models.TextField(blank=True, null=True)
    inappropriateness_1 = models.TextField(blank=True, null=True)
    corrections_1 = models.TextField(blank=True, null=True)
    corrected_response_1 = models.TextField(blank=True, null=True)

    response_2 = models.TextField(blank=True, null=True)
    redundancies_2 = models.TextField(blank=True, null=True)
    inappropriateness_2 = models.TextField(blank=True, null=True)
    corrections_2 = models.TextField(blank=True, null=True)
    corrected_response_2 = models.TextField(blank=True, null=True)

    response_3 = models.TextField(blank=True, null=True)
    redundancies_3 = models.TextField(blank=True, null=True)
    inappropriateness_3 = models.TextField(blank=True, null=True)
    corrections_3 = models.TextField(blank=True, null=True)
    corrected_response_3 = models.TextField(blank=True, null=True)

    response_4 = models.TextField(blank=True, null=True)
    redundancies_4 = models.TextField(blank=True, null=True)
    inappropriateness_4 = models.TextField(blank=True, null=True)
    corrections_4 = models.TextField(blank=True, null=True)
    corrected_response_4 = models.TextField(blank=True, null=True)

    response_5 = models.TextField(blank=True, null=True)
    redundancies_5 = models.TextField(blank=True, null=True)
    inappropriateness_5 = models.TextField(blank=True, null=True)
    corrections_5 = models.TextField(blank=True, null=True)
    corrected_response_5 = models.TextField(blank=True, null=True)

    response_6 = models.TextField(blank=True, null=True)
    redundancies_6 = models.TextField(blank=True, null=True)
    inappropriateness_6 = models.TextField(blank=True, null=True)
    corrections_6 = models.TextField(blank=True, null=True)
    corrected_response_6 = models.TextField(blank=True, null=True)

    response_7 = models.TextField(blank=True, null=True)
    redundancies_7 = models.TextField(blank=True, null=True)
    inappropriateness_7 = models.TextField(blank=True, null=True)
    corrections_7 = models.TextField(blank=True, null=True)
    corrected_response_7 = models.TextField(blank=True, null=True)

    response_8 = models.TextField(blank=True, null=True)
    redundancies_8 = models.TextField(blank=True, null=True)
    inappropriateness_8 = models.TextField(blank=True, null=True)
    corrections_8 = models.TextField(blank=True, null=True)
    corrected_response_8 = models.TextField(blank=True, null=True)

    response_9 = models.TextField(blank=True, null=True)
    redundancies_9 = models.TextField(blank=True, null=True)
    inappropriateness_9 = models.TextField(blank=True, null=True)
    corrections_9 = models.TextField(blank=True, null=True)
    corrected_response_9 = models.TextField(blank=True, null=True)

    response_10 = models.TextField(blank=True, null=True)
    redundancies_10 = models.TextField(blank=True, null=True)
    inappropriateness_10 = models.TextField(blank=True, null=True)
    corrections_10 = models.TextField(blank=True, null=True)
    corrected_response_10 = models.TextField(blank=True, null=True)

    # 인터뷰 전체에 대한 총평을 저장할 필드 추가
    overall_feedback = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)


    # 이서 필드
    # 음성 분석 결과 저장을 위한 필드 추가
         # 이서 필드
   
class voiceAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    question_list = models.ForeignKey(QuestionLists, on_delete=models.CASCADE, null=True)  # QuestionLists 모델 참조
    pitch_graph = models.TextField(blank=True, null=True)  # Base64 인코딩된 이미지 데이터를 텍스트 필드에 저장
    intensity_graph = models.TextField(blank=True, null=True)  # Base64 인코딩된 이미지 데이터를 텍스트 필드에 저장
    pitch_summary = models.CharField(max_length=255, blank=True, null=True)
    intensity_summary = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"InterviewAnalysis for {self.user.username} at {self.created_at}"
