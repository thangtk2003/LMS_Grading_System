from django import forms
from .models import Submission, Exercise

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['code']


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['title', 'description', 'test_cases']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'test_cases': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }