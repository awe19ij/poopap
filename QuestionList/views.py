from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import QuestionLists, ProblemSolvingQuestion, CommunicationSkillQuestion, GrowthPotentialQuestion, PersonalityTraitQuestion
import random
import requests
import logging

logger = logging.getLogger(__name__)

class ChatGPTView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.debug("Received data: %s", request.data)
        user_input_field = request.data.get('input_field', '')
        user_input_job = request.data.get('input_job', '')
        selected_categories = request.data.get('selected_directions', [])

        if not user_input_field or not user_input_job:
            logger.error("Missing input field or job")
            return Response({"error": "분야와 직무 입력은 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        modified_input = f"{user_input_field}분야의 {user_input_job}직무와 관련된 면접 질문 10가지 리스트업해줘 한국어로"
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": "gpt-3.5-turbo-0125", "messages": [{"role": "user", "content": modified_input}]},
                timeout=10
            )
            response.raise_for_status()
            job_related_questions = response.json().get('choices')[0].get('message').get('content').splitlines()
            job_related_questions = [q.strip() for q in job_related_questions if q.strip()]
        except requests.exceptions.RequestException as e:
            logger.error("Error contacting OpenAI API: %s", str(e))
            return Response({"error": f"서버 오류: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        all_questions = set(job_related_questions[:10])  # 중복 제거를 위해 집합 사용

        category_models = {
            'problem_solving': ProblemSolvingQuestion,
            'communication_skills': CommunicationSkillQuestion,
            'growth_potential': GrowthPotentialQuestion,
            'personality_traits': PersonalityTraitQuestion
        }

        for category in selected_categories:
            if category in category_models:
                model = category_models[category]
                questions = list(model.objects.all().values_list('question', flat=True))
                if questions:  # 해당 카테고리에 질문이 있는 경우에만 처리
                    random_questions = random.sample(questions, min(len(questions), 3))
                    all_questions.update(random_questions)  # 집합에 추가하여 중복 방지

        if len(all_questions) > 10:
            all_questions = random.sample(list(all_questions), 10)  # 리스트로 변환 후 10개 선택

        question_list = QuestionLists(user=request.user)
        for i, question in enumerate(all_questions, 1):
            question_text = question.split('.', 1)[-1].strip() if '.' in question else question
            setattr(question_list, f'question_{i}', question_text)
        question_list.save()

        sorted_questions = [getattr(question_list, f'question_{i}') for i in range(1, 11)]
        logger.info("Processing complete")
        return Response({"id": question_list.id, "questions": sorted_questions}, status=status.HTTP_201_CREATED)
