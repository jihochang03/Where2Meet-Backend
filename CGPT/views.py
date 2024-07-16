from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
import openai
import os
from dotenv import load_dotenv
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Factor 키워드 매핑
factor_keywords = {
    'factor_2': 'mz세대의 핫플',
    'factor_3': '밥집',
    'factor_4': '카페',
    'factor_5': '술집',
    'factor_6': '액티비티',
    'factor_7': '쇼핑',
}

# chatgpt에 넣기
def get_completion(prompt):
    query = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    response = query.choices[0].message["content"]
    return response

class QueryView(APIView):
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        operation_description="Get GPT-3.5 completion for a given station and selected factors",
        manual_parameters=[
            openapi.Parameter('station_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Name of the station'),
            openapi.Parameter('factor', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Factors to consider', style='form', explode=True, enum=['factor_2', 'factor_3', 'factor_4', 'factor_5', 'factor_6', 'factor_7'])
        ],
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'response': openapi.Schema(type=openapi.TYPE_STRING, description='Summary response from GPT-3.5'),
                }
            ),
            status.HTTP_400_BAD_REQUEST: 'Invalid query parameters',
        }
    )
    def get(self, request, format=None):
        station_name = request.query_params.get('station_name')
        factors = request.query_params.getlist('factor')
        print(factors)
        if not station_name or not factors:
            return Response({'error': 'station_name and at least one factor are required'}, status=status.HTTP_400_BAD_REQUEST)

        factor_keywords_list = [factor_keywords[factor] for factor in factors]
        factors_string = ', '.join(factor_keywords_list)
        prompt = f"약속장소로 '{station_name}'이 적합한 이유를 '{factors_string}' 관점에서 한줄로 설명해줘."
        print(prompt)
        response = get_completion(prompt)
        return Response({'response': response})

