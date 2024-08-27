from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import start_gaze_tracking_view, stop_gaze_tracking_view, SignedURLView, VideoUploadView

urlpatterns = [
    path('start/<int:user_id>/<int:interview_id>/', start_gaze_tracking_view, name='start_gaze_tracking'),
    path('stop/<int:user_id>/<int:interview_id>/', stop_gaze_tracking_view, name='stop_gaze_tracking'),
    path('generate-signed-url/<int:user_id>/<int:interview_id>/', SignedURLView.as_view(), name='generate_signed_url'),
    path('upload-video/<int:user_id>/<int:interview_id>/', VideoUploadView.as_view(), name='upload_video'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
