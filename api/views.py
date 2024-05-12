from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response

from api.openai_connect import OpenAIConnect
from api.models import MealTypes
import json


class InvalidMealType(APIException):
    status_code = 400
    default_detail = "Invalid meal type"
    default_code = 'invalid_meal_type'


class GetTextResponse(APIView):
    @staticmethod
    def post(request):
        prompt = request.data.get("prompt")
        meal_type = request.data.get("meal_type")
        if meal_type not in MealTypes.values:
            raise InvalidMealType()

        openai_connect = OpenAIConnect()
        response = openai_connect.get_response(prompt)
        return Response(json.loads(response))
