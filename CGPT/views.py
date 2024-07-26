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
    '2': 'MZ세대에게 인기 있는 곳',
    '3': '맛있는 밥집이 많은 곳',
    '4': '아름다운 카페들이 있는 곳',
    '5': '멋진 술집이 많은 곳',
    '6': '재미있는 액티비티를 즐길 수 있는 곳',
    '7': '쇼핑하기 좋은 곳',
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
        view_type = request.query_params.get('view_type')  # 'pc' 또는 'mobile'
    
        if not station_name:
            return Response({'error': 'station_name과 적어도 하나의 factor가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
        factor_keywords_list = [factor_keywords[factor] for factor in factors]
        factors_string = ', '.join(factor_keywords_list)
        if not factors_string:
            if view_type == 'pc':
                prompt = f"만나는 장소로 '{station_name}'이 적합한 이유를 '{factors_string}' 관점에서 2~3문장으로 설명해주세요. 만나는 장소를 추천하는 느낌으로 자연스럽지만 존댓말로 말해주고 그 역의 특성이나 역 주변 유명한 들도 함께 언급해주면 좋겠어요."
            else:  # 모바일 버전
                prompt = f"만나는 장소로 '{station_name}'이 적합한 이유를 '{factors_string}' 관점에서 한 문장으로 요약해세요. 만나는 장소를 추천하는 느낌으로 자연스럽지만 존댓말로 말해주고 그 역의 특성이나 역 주변 유명한 것들도 함께 언급해주면 좋겠어요. "
        else: 
            if view_type == 'pc':
                prompt = f"만나는 장소로 '{station_name}'이 적합한 이유를 2~3문장으로 설명해주세요. 만나는 장소를 추천하는 느낌으로 자연스럽지만 존댓말로 말해주고 그 역의 특성이나 역 주변 유명한 들도 함께 언급해주면 좋겠어요."
            else:  # 모바일 버전
                prompt = f"만나는 장소로 '{station_name}'이 적합한 이유를 한 문장으로 요약해주세요. 만나는 장소를 추천하는 느낌으로 자연스럽지만 존댓말로 말해주고 그 역의 특성이나 역 주변 유명한 것들도 함께 언급해주면 좋겠어요."
        response = get_completion(prompt)
        return Response({'response': response})
