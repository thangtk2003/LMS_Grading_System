from django.contrib import admin
from .models import Exercise, Submission

# Register your models here.
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'student', 'created_at', 'score')
    search_fields = ('exercise__title', 'submission__student')
    list_filter = ('exercise',)
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('exercise', 'student')