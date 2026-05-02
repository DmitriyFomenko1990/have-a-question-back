from django.urls import path

from .views import (
    QuestionDetailView,
    QuestionListCreateView,
    QuestionRespondView,
    QuestionResultsView,
    MyQuestionListView
)


urlpatterns = [
    path("questions/", QuestionListCreateView.as_view(), name="question-list-create"),
    path("questions/my/", MyQuestionListView.as_view(), name="my-question-list"),
    path("questions/<int:pk>/", QuestionDetailView.as_view(), name="question-detail"),
    path("questions/<int:pk>/respond/", QuestionRespondView.as_view(), name="question-respond"),
    path("questions/<int:pk>/results/", QuestionResultsView.as_view(), name="question-results"),
]