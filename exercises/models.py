from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Exercise(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    test_cases = models.TextField(help_text="Define test cases as Python code")

    def __str__(self):
        return self.title

class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    code = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.exercise.title}"
