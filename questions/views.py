from django.db.models import Count, OuterRef, Exists, Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import Question, QuestionOption, QuestionResponse
from .serializers import (
    QuestionCreateSerializer,
    QuestionDetailSerializer,
    QuestionListSerializer,
    QuestionRespondSerializer,
    QuestionResponseSerializer,
    QuestionSearchSerializer,
)

def get_questions_queryset(user):
       user_responses = QuestionResponse.objects.filter(
            question=OuterRef("pk"),
            user=user,
       )

       return (
            Question.objects.filter(is_active=True)
            .select_related("author")
            .prefetch_related("options")
            .annotate(
                options_count=Count("options", distinct=True),
                responses_count=Count("responses", distinct=True),
                has_answered=Exists(user_responses),
            )
      )


class QuestionListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return get_questions_queryset(self.request.user).exclude(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuestionCreateSerializer

        return QuestionListSerializer

class MyQuestionListView(generics.ListAPIView):
    serializer_class = QuestionListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return get_questions_queryset(self.request.user).filter(author=self.request.user)


class QuestionSearchView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=QuestionSearchSerializer,
        responses=QuestionListSerializer(many=True),
        summary="Search questions",
        description="Search, filter, and sort questions available to the current user.",
    )

    def post(self, request):
        serializer = QuestionSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        search = serializer.validated_data.get("search", "").strip()
        answered = serializer.validated_data.get("answered", "all")
        sort = serializer.validated_data.get("sort", "")
        sort_type = serializer.validated_data.get("sort_type", "default")

        queryset = get_questions_queryset(request.user).exclude(author=request.user)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        if answered == "true":
            queryset = queryset.filter(has_answered=True)

        if answered == "false":
            queryset = queryset.filter(has_answered=False)

        if sort_type == "asc":
            queryset = queryset.order_by(sort)

        if sort_type == "desc":
            queryset = queryset.order_by(f"-{sort}")

        output_serializer = QuestionListSerializer(
            queryset,
            many=True,
            context={"request": request},
        )

        return Response(output_serializer.data)



class QuestionDetailView(generics.RetrieveAPIView):
    serializer_class = QuestionDetailSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Question.objects.filter(is_active=True)
            .select_related("author")
            .prefetch_related("options")
        )


class QuestionRespondView(generics.CreateAPIView):
    serializer_class = QuestionRespondSerializer
    permission_classes = (IsAuthenticated,)

    def get_question(self):
        return generics.get_object_or_404(Question, pk=self.kwargs["pk"], is_active=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["question"] = self.get_question()

        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        output_serializer = QuestionResponseSerializer(response)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class QuestionResultsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        question = generics.get_object_or_404(
            Question.objects.prefetch_related("options", "responses"),
            pk=pk,
            is_active=True,
        )
        total_responses = question.responses.count()
        options = []

        for option in question.options.all():
            count = QuestionResponse.objects.filter(selected_options__option=option).count()
            percent = round((count / total_responses) * 100, 2) if total_responses else 0

            options.append(
                {
                    "id": option.id,
                    "text": option.text,
                    "count": count,
                    "percent": percent,
                }
            )

        custom_answers = [
            {
                "user": response.user.username,
                "text": response.custom_answer_text,
                "created_at": response.created_at,
            }
            for response in question.responses.select_related("user").exclude(custom_answer_text="")
        ]

        return Response(
            {
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "choice_type": question.choice_type,
                    "allow_custom_answer": question.allow_custom_answer,
                },
                "total_responses": total_responses,
                "options": options,
                "custom_answers": custom_answers,
            }
        )