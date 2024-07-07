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
        operation_description="Get GPT-3.5 completion for a given prompt",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'prompt': openapi.Schema(type=openapi.TYPE_STRING, description='Prompt to send to GPT-3.5'),
            },
            required=['prompt'],
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'response': openapi.Schema(type=openapi.TYPE_STRING, description='Response from GPT-3.5'),
                }
            ),
            status.HTTP_400_BAD_REQUEST: 'Prompt is required',
        }
    )
    def post(self, request, format=None):
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({'error': 'Prompt is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        response = get_completion(prompt)
        return Response({'response': response})
