from rest_framework import serializers

from .models import Question, QuestionOption, QuestionResponse, QuestionResponseOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ("id", "text")


class QuestionListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    options_count = serializers.IntegerField(read_only=True)
    responses_count = serializers.IntegerField(read_only=True)
    options = QuestionOptionSerializer(many=True, read_only=True)
    has_answered = serializers.BooleanField(read_only=True)
    answered_options = serializers.SerializerMethodField()
    answered_custom_text = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            "id",
            "author",
            "title",
            "description",
            "choice_type",
            "allow_custom_answer",
            "is_active",
            "options_count",
            "responses_count",
            "options",
            "has_answered",
            "answered_options",
            "answered_custom_text",
            "created_at",
            "updated_at",
        )

        
    def get_user_response(self, question):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return None

        return (
            QuestionResponse.objects.filter(question=question, user=request.user)
            .prefetch_related("selected_options__option")
            .first()
        )

    def get_answered_options(self, question):
        response = self.get_user_response(question)

        if not response:
            return []

        options = [
            selected_option.option
            for selected_option in response.selected_options.all()
        ]

        return QuestionOptionSerializer(options, many=True).data

    def get_answered_custom_text(self, question):
        response = self.get_user_response(question)

        if not response:
            return ""

        return response.custom_answer_text


class QuestionSearchSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    answered = serializers.ChoiceField(
        choices=("all", "true", "false"),
        required=False,
        default="all",
    )
    sort = serializers.ChoiceField(
        choices=("created_at", "responses_count"),
        required=False,
        allow_blank=True,
        default="",
    )

    sort_type = serializers.ChoiceField(
        choices=("default", "asc", "desc"),
        required=False,
        default="default",
    )

    def validate(self, attrs):
        sort = attrs.get("sort", "" )
        sort_type = attrs.get("sort_type", "default")

        if sort_type in ("asc", "desc") and not sort:
            raise serializers.ValidationError("Sort must be provided when sort type is not default")

        if sort_type == "default":
            attrs["sort"] = ""

        return attrs

    


class QuestionDetailSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = (
            "id",
            "author",
            "title",
            "description",
            "choice_type",
            "allow_custom_answer",
            "is_active",
            "options",
            "created_at",
            "updated_at",
        )



class QuestionCreateSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = (
            "id",
            "title",
            "description",
            "choice_type",
            "allow_custom_answer",
            "options",
        )
        read_only_fields = ("id",)

    def validate_options(self, options):
        if len(options) < 2:
            raise serializers.ValidationError("Question must have at least two options")

        return options

    def create(self, validated_data):
        options_data = validated_data.pop("options")
        question = Question.objects.create(
            author=self.context["request"].user,
            **validated_data,
        )

        for option_data in options_data:
            QuestionOption.objects.create(question=question, **option_data)

        return question


class QuestionResponseOptionSerializer(serializers.ModelSerializer):
    option = QuestionOptionSerializer(read_only=True)

    class Meta:
        model = QuestionResponseOption
        fields = ("id", "option", "created_at")


class QuestionResponseSerializer(serializers.ModelSerializer):
    selected_options = QuestionResponseOptionSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionResponse
        fields = (
            "id",
            "question",
            "user",
            "custom_answer_text",
            "selected_options",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "question", "user", "selected_options", "created_at", "updated_at")


class QuestionRespondSerializer(serializers.Serializer):
    option_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )
    custom_answer_text = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        question = self.context["question"]
        user = self.context["request"].user
        option_ids = attrs.get("option_ids", [])
        custom_answer_text = attrs.get("custom_answer_text", "").strip()

        if question.author == user:
            raise serializers.ValidationError("Author cannot respond to own question")

        if QuestionResponse.objects.filter(question=question, user=user).exists():
            raise serializers.ValidationError("You have already responded to this question")

        if not option_ids and not custom_answer_text:
            raise serializers.ValidationError("Select at least one option or provide custom answer")

        if question.choice_type == Question.ChoiceType.SINGLE and len(option_ids) > 1:
            raise serializers.ValidationError("Single choice question accepts only one option")

        if custom_answer_text and not question.allow_custom_answer:
            raise serializers.ValidationError("Custom answer is not allowed for this question")

        existing_options_count = QuestionOption.objects.filter(
            question=question,
            id__in=option_ids,
        ).count()

        if existing_options_count != len(set(option_ids)):
            raise serializers.ValidationError("One or more options do not belong to this question")

        attrs["option_ids"] = list(dict.fromkeys(option_ids))
        attrs["custom_answer_text"] = custom_answer_text

        return attrs

    def create(self, validated_data):
        question = self.context["question"]
        user = self.context["request"].user
        option_ids = validated_data.get("option_ids", [])
        custom_answer_text = validated_data.get("custom_answer_text", "")

        response = QuestionResponse.objects.create(
            question=question,
            user=user,
            custom_answer_text=custom_answer_text,
        )

        for option_id in option_ids:
            QuestionResponseOption.objects.create(
                response=response,
                option_id=option_id,
            )

        return response