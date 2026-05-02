from django.contrib import admin

from .models import Question, QuestionOption, QuestionResponse, QuestionResponseOption


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "choice_type", "allow_custom_answer", "is_active", "created_at")
    list_filter = ("choice_type", "allow_custom_answer", "is_active", "created_at")
    search_fields = ("title", "description", "author__email", "author__username")
    inlines = (QuestionOptionInline,)
    readonly_fields = ("created_at", "updated_at")


class QuestionResponseOptionInline(admin.TabularInline):
    model = QuestionResponseOption
    extra = 0


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ("question", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("question__title", "user__email", "user__username", "custom_answer_text")
    inlines = (QuestionResponseOptionInline,)
    readonly_fields = ("created_at", "updated_at")


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "created_at")
    search_fields = ("text", "question__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(QuestionResponseOption)
class QuestionResponseOptionAdmin(admin.ModelAdmin):
    list_display = ("response", "option", "created_at")
    search_fields = ("response__question__title", "option__text")
    readonly_fields = ("created_at",)