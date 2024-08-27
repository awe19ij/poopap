from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from .models import InterviewAnalysis, QuestionLists, voiceAnalysis
import os
from django.conf import settings
import logging
import requests
from .serializers import *



# 이서 import 항목
from google.cloud import speech
from google.cloud import storage
from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser, FormParser
from google.cloud.speech import RecognitionConfig, RecognitionAudio
from google.oauth2 import service_account
from django.conf import settings
from pydub import AudioSegment
import nltk
from nltk.tokenize import word_tokenize
import difflib
import parselmouth
import numpy as np
import base64
import io
import re
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import nltk
import matplotlib
from pathlib import Path
matplotlib.use('Agg')  # 백엔드를 Agg로 설정
from rest_framework import status
from pydub import AudioSegment
from io import BytesIO
import matplotlib.pyplot as plt
import tempfile 

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from .models import InterviewAnalysis, QuestionLists
import os
from django.conf import settings
import logging
import requests
import re
import time

from rest_framework import status
from pydub import AudioSegment
from io import BytesIO
import parselmouth
import matplotlib.pyplot as plt
import numpy as np
import base64
import tempfile 
import datetime  # 날짜와 시간을 다루기 위해 필요
from google.cloud.exceptions import GoogleCloudError  # Google Cloud에서 발생하는 예외 처리에 필요


logger = logging.getLogger(__name__)


# 답변 스크립트 분석
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from .models import InterviewAnalysis, QuestionLists
import os
from django.conf import settings
import logging
import requests
import binascii
from Users.models import User

logger = logging.getLogger(__name__)

class ResponseAPIView(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id, interview_id):
        user = get_object_or_404(User, id=user_id)
        question_list = get_object_or_404(QuestionLists, id=interview_id)
        interview_response = InterviewAnalysis(question_list=question_list)

        # 로그인한 사용자를 user 필드에 할당
        interview_response.user = request.user

        base_dir = settings.BASE_DIR
        redundant_expressions_path = os.path.join(base_dir, 'InterviewAnalyze', 'redundant_expressions.txt')
        inappropriate_terms_path = os.path.join(base_dir, 'InterviewAnalyze', 'inappropriate_terms.txt')

        try:
            with open(redundant_expressions_path, 'r') as file:
                redundant_expressions = file.read().splitlines()
            with open(inappropriate_terms_path, 'r') as file:
                inappropriate_terms = dict(line.strip().split(':') for line in file if ':' in line)
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return Response({"error": "Required file not found"}, status=500)

        response_data = []
        all_responses = ""
        for i in range(1, 11):
            script_key = f'script_{i}'
            response_key = f'response_{i}'
            question_key = f'question_{i}'
            script_text = request.data.get(script_key, "")
            question_text = getattr(question_list, question_key, "")

            # 잉여 표현과 부적절한 표현을 분석
            found_redundant = self.find_redundant_expressions(script_text, redundant_expressions)
            corrections = {}
            corrected_text = script_text
            for term, replacement in inappropriate_terms.items():
                if term in script_text:
                    corrections[term] = replacement
                    corrected_text = corrected_text.replace(term, replacement)

            setattr(interview_response, f'response_{i}', script_text)
            setattr(interview_response, f'redundancies_{i}', ', '.join(found_redundant))
            setattr(interview_response, f'inappropriateness_{i}', ', '.join(corrections.keys()))
            setattr(interview_response, f'corrections_{i}', str(corrections))
            setattr(interview_response, f'corrected_response_{i}', corrected_text)

            response_data.append({
                'question': question_text,
                'response': script_text,
                'redundancies': found_redundant,
                'inappropriateness': list(corrections.keys()),
                'corrections': corrections
            })

            if script_text:
                all_responses += f"{script_text}\n"

        interview_response.save()

        prompt = f"다음은 사용자의 면접 응답입니다:\n{all_responses}\n\n응답이 직무연관성, 문제해결력, 의사소통능력, 성장가능성, 인성과 관련하여 적절했는지 300자 내외로 총평을 작성해줘."
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": "gpt-3.5-turbo-0125", "messages": [{"role": "user", "content": prompt}]},
                timeout=10
            )
            response.raise_for_status()
            gpt_feedback = response.json().get('choices')[0].get('message').get('content')
            interview_response.overall_feedback = gpt_feedback  # 총평을 overall_feedback 필드에 저장
        except requests.exceptions.RequestException as e:
            logger.error(f"GPT API request failed: {e}")
            gpt_feedback = "총평을 가져오는 데 실패했습니다."
            interview_response.overall_feedback = gpt_feedback  # 실패 메시지를 저장

        interview_response.save()  # 변경 사항 저장

        return Response({
            'interview_id': interview_response.id,
            'responses': response_data,
            'gpt_feedback': gpt_feedback
        }, status=200)

    def find_redundant_expressions(self, script_text, redundant_expressions):
        # 스크립트를 공백을 기준으로 단어 단위로 분할
        words = script_text.split()
        redundancies = [word for word in words if word in redundant_expressions]
        return redundancies


# 이서 mp3 받아오기 위한 스토리지 관련 설정
# def generate_signed_url(bucket_name, blob_name, expiration=86400):
#     client = storage.Client()
#     try:
#         bucket = client.bucket(bucket_name)
#         blob = bucket.blob(blob_name)
#         url = blob.generate_signed_url(
#             expiration=datetime.timedelta(seconds=expiration),
#             method='PUT',
#             content_type='audio/mp3'  # MP3 파일에 맞는 콘텐츠 타입 설정
#         )
#         return url
#     except GoogleCloudError as e:
#         raise ValueError(f"Failed to generate signed URL: {e}")
#     except Exception as e:
#         raise ValueError(f"Unexpected error while generating signed URL: {e}")

# class VoiceSignedURLView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser, JSONParser]

#     def post(self, request, user_id, interview_id, *args, **kwargs):
#         serializer = SignedURLSerializer(data=request.data)
#         if serializer.is_valid():
#             bucket_name = settings.GS_BUCKET_NAME
#             try:
#                 signed_urls = {}
#                 for i in range(1, 3):  # 두 개의 MP3 파일을 위한 루프
#                     blob_name = f"voice/{user_id}/{interview_id}/{i}.mp3"
#                     signed_url = generate_signed_url(bucket_name, blob_name)
#                     signed_urls[f"file_{i}"] = signed_url
                
#                 return Response({"signed_urls": signed_urls}, status=200)
#             except ValueError as e:
#                 return Response({"message": str(e)}, status=500)
#         else:
#             return Response(serializer.errors, status=400)


# 여기서부터 이서코드
nltk.download('punkt') # 1회만 다운로드 하면댐

def set_korean_font():
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'NanumGothic.ttf')
    if not os.path.isfile(font_path):
        raise RuntimeError(f"Font file not found: {font_path}")
    font_prop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=font_prop.get_name())

credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
) 


class VoiceAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # 파일 업로드를 위해 MultiPartParser와 FormParser 사용
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        question_id = kwargs.get('question_id')  # question_id를 사용하여 question_list를 가져옵니다.

        user = get_object_or_404(User, id=user_id)
        question_list = get_object_or_404(QuestionLists, id=question_id)  # QuestionLists 모델에서 객체를 가져옵니다.
        action = request.query_params.get('action', 'upload')  # 쿼리 파라미터로 'action' 값을 가져오고 기본값은 'upload'

        if action == 'upload':
            return self.upload_file(request)  # 파일 업로드 처리
        elif action == 'merge':
            return self.merge_files_and_analyze(request, question_list)  # 파일 병합 및 분석 처리
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)  # 유효하지 않은 action 처리

    # 음성 파일 받기
    def upload_file(self, request):
        uploaded_files = request.FILES.getlist('files')
        if not uploaded_files:
            return Response({"error": "No files uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # 파일 데이터를 메모리에 저장
        temp_file_data = []
        for file in uploaded_files:
            file_data = file.read()
            temp_file_data.append(base64.b64encode(file_data).decode('utf-8'))
            
        return Response({"file_data": temp_file_data}, status=status.HTTP_201_CREATED)

    def merge_files_and_analyze(self, request, question_list):
        temp_file_data = request.data.get('file_data')
        if not temp_file_data:
            return Response({"error": "No files to merge"}, status=status.HTTP_400_BAD_REQUEST)

        # 리스트 빈칸 
        if not isinstance(temp_file_data, list) or len(temp_file_data) == 0:
            return Response({"error": "Invalid file data format or no data provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 로깅 추가 400 
        for i, file_data in enumerate(temp_file_data):
            if not file_data:
                return Response({"error": f"File data at index {i} is empty or invalid"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            combined = AudioSegment.empty()
            for i, file_data in enumerate(temp_file_data):
                try:
                    file_data = correct_base64_padding(file_data)
                    if not is_valid_base64(file_data):
                        raise ValueError("Invalid Base64 data")
                    file_data = base64.b64decode(file_data.encode('utf-8'))
                    audio = AudioSegment.from_file(BytesIO(file_data), format="mp3")
                    combined += audio
                except (binascii.Error, ValueError) as e:
                    return Response({"error": f"Invalid Base64 data at index {i}: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"error": f"Error processing file index {i}: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


            # 병합된 파일을 WAV 형식으로 변환
            wav_file = BytesIO()
            combined.export(wav_file, format="wav")
            wav_file.seek(0)
            
            # 임시 파일에 저장
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
                temp_wav_file.write(wav_file.read())
                temp_wav_file_path = temp_wav_file.name

            # WAV 파일을 모노로 변환
            audio_segment = AudioSegment.from_file(temp_wav_file_path, format="wav")
            audio_segment = audio_segment.set_channels(1)
            wav_file = BytesIO()
            audio_segment.export(wav_file, format="wav")
            wav_file.seek(0)

            # 분석 작업
            analysis_result = self.analyze_audio(temp_wav_file_path)
            
            # 임시 파일 삭제
            os.remove(temp_wav_file_path)
            
            # 데이터베이스에 분석 결과 저장
            interview_analysis = voiceAnalysis(
                user=request.user,
                question_list=question_list,  # question_list로 교체합니다.
                pitch_graph=analysis_result["pitch_graph"],
                intensity_graph=analysis_result["intensity_graph"],
                pitch_summary=analysis_result["pitch_summary"],
                intensity_summary=analysis_result["intensity_summary"],
            )
            interview_analysis.save()

            return Response(analysis_result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def analyze_audio(self, wav_file_path):
        snd = parselmouth.Sound(wav_file_path)
        pitch = snd.to_pitch()
        intensity = snd.to_intensity()

        pitch_values = pitch.selected_array['frequency']
        intensity_values = intensity.values.T

        pitch_mean = np.mean(pitch_values[pitch_values > 0])
        intensity_mean = np.mean(intensity_values)

        # 피치 그래프 생성
        pitch_fig, pitch_ax = plt.subplots()
        pitch_ax.plot(pitch.xs(), pitch_values, 'o', markersize=2)
        pitch_ax.set_xlabel("Time [s]")
        pitch_ax.set_ylabel("Pitch [Hz]")
        pitch_ax.set_title("Pitch Analysis")
        pitch_graph = self.fig_to_base64(pitch_fig)

        # 강도 그래프 생성
        intensity_fig, intensity_ax = plt.subplots()
        intensity_ax.plot(intensity.xs(), intensity_values, 'o', markersize=2)
        intensity_ax.set_xlabel("Time [s]")
        intensity_ax.set_ylabel("Intensity [dB]")
        intensity_ax.set_title("Intensity Analysis")
        intensity_graph = self.fig_to_base64(intensity_fig)

        # 총평 생성
        pitch_summary = self.get_pitch_summary(pitch_mean)
        intensity_summary = self.get_intensity_summary(intensity_mean)

        analysis_result = {
            "pitch_graph": pitch_graph,
            "intensity_graph": intensity_graph,
            "pitch_summary": pitch_summary,
            "intensity_summary": intensity_summary,
        }

        return analysis_result

    def fig_to_base64(self, fig):
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        fig_data = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return fig_data

    def get_pitch_summary(self, pitch_mean):
        if pitch_mean >= 450:
            return "님 시끄러움"
        elif pitch_mean >= 150:
            return "님은 평범함 ㅇㅇ"
        else:
            return "개미소리"

    def get_intensity_summary(self, intensity_mean):
        if intensity_mean >= 65:
            return "빠르게 말하고 계시네요"
        elif intensity_mean >= 35:
            return "님의 말하기 속도는 평범해요"
        else:
            return "님은 아주 느리게 말함"

def correct_base64_padding(base64_string):
    return base64_string + '=' * (4 - len(base64_string) % 4)

def is_valid_base64(base64_string):
    try:
        if isinstance(base64_string, str):
            base64.b64decode(base64_string.encode('utf-8'))
            return True
    except binascii.Error:
        return False
    return False
