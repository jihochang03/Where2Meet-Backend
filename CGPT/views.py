from django.shortcuts import render 
from django.http import JsonResponse 
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_completion(prompt): 
    print(prompt) 
    query = openai.ChatCompletion.create( 
        model="gpt-3.5-turbo",
        messages=[
            {'role':'user','content': prompt}
        ], 
        max_tokens=1024, 
        n=1, 
        stop=None, 
        temperature=0.5, 
    ) 
    response = query.choices[0].message["content"]
    print(response) 
    return response 

def query_view(request): 
    if request.method == 'POST': 
        prompt = request.POST.get('prompt') 
        prompt = str(prompt)
        print(f"prompt={prompt}")
        response = get_completion(prompt)
        return JsonResponse({'response': response}) 
    return render(request, 'index.html') 
