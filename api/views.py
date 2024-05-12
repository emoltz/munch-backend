from rest_framework.views import APIView
from rest_framework.response import Response
from api.openai_connect import OpenAIConnect
import json

class GetTextResponse(APIView):
    @staticmethod
    def post(request):
        prompt = request.data.get("prompt")
        openai_connect = OpenAIConnect()
        response = openai_connect.get_response(prompt)
        return Response(json.loads(response))