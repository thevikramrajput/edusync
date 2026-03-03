"""
EduSync — Feedback Admin.
"""
from django.contrib import admin
from .models import ParentFeedbackQuestion, ParentFeedbackResponse


@admin.register(ParentFeedbackQuestion)
class ParentFeedbackQuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text", "category", "order"]
    list_filter = ["category"]


@admin.register(ParentFeedbackResponse)
class ParentFeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ["student", "question", "quarter"]
    list_filter = ["quarter"]
