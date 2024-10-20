from django.contrib import admin
from .models import Exercise, Submission
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# Define resource classes for import/export
class ExerciseResource(resources.ModelResource):
    class Meta:
        model = Exercise
        fields = ('id', 'title', 'description', 'language', 'test_cases')

class SubmissionResource(resources.ModelResource):
    class Meta:
        model = Submission
        fields = ('id', 'student__username', 'exercise__title', 'code', 'created_at', 'score')

# Register the models with ImportExportModelAdmin
@admin.register(Exercise)
class ExerciseAdmin(ImportExportModelAdmin):
    list_display = ('title', 'description', 'language')
    search_fields = ('title',)
    resource_class = ExerciseResource

@admin.register(Submission)
class SubmissionAdmin(ImportExportModelAdmin):
    resource_class = SubmissionResource
    list_display = ('exercise', 'student', 'created_at', 'score')
    search_fields = ('exercise__title', 'student__username')
    list_filter = ('exercise',)
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('exercise', 'student')
