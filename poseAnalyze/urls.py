# URL 패턴 설정
from django.urls import path
from .views import GetSignedURLView

urlpatterns = [
    path('generate-signed-url/<int:user_id>/<int:interview_id>/', GetSignedURLView.as_view(), name='generate_signed_url'),
]
