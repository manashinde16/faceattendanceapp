from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    face_encoding = models.TextField()
    aadhaar = models.CharField(max_length=12, unique=True)
    password = models.CharField(max_length=128, default='defaultpass')
    image = models.ImageField(upload_to='user_images/', null=True, blank=True)  # 👈 Add this line
    face_encoding = models.TextField()

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='Present')
