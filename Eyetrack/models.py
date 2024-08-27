# models.py
from django.db import models
from django.conf import settings

class GazeTrackingResult(models.Model):
    #image = models.ImageField(upload_to='gaze_images/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    interview_id = models.IntegerField(default=1) 
    encoded_image = models.TextField()
    feedback = models.TextField(default="No feedback provided.") 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GazeTrackingResult #{self.id}for User #{self.user_id} Interview #{self.interview_id}"


# 프론트에서 받아오는 Video 저장되는 모델
class Video(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="videos", null=True)
    interview_id = models.IntegerField(null=True)
    file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video {self.id} for User {self.user.id if self.user else 'None'} Interview {self.interview_id}"
