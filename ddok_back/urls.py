from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('interview_questions/', include('QuestionList.urls')),
    path('users/', include('Users.urls')),
    path('interview/', include('InterviewAnalyze.urls')),
    path('mylog/', include("myLog.urls")),
    path('eyetrack/', include('Eyetrack.urls')),
    path('pose/', include('poseAnalyze.urls'))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
