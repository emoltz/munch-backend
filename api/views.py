from datetime import datetime

from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from dataclasses import dataclass
from api.openai_connect import OpenAIConnect
from api.models import MealTypes, Food
import json

from api.serializers import FoodSerializer


class InvalidMealType(APIException):
    status_code = 400
    default_detail = "Invalid meal type"
    default_code = 'invalid_meal_type'


class ErrorMessage(APIException):
    def __init__(self, message):
        self.status_code = 400
        self.default_detail = message
        self.default_code = 'error'


class GetTextResponse(APIView):

    @dataclass
    class RequestArgs:
        """
        For reference only. Not used in the code.
        """
        description: str
        meal_type: str
        date: str or None  # YYYY-MM-DD "2024-05-12"
        meal_name: str or None

    @staticmethod
    def post(request):
        description = request.data.get("description")
        meal_type = request.data.get("meal_type")
        date = request.data.get("date")
        meal_name = request.data.get("meal_name")


        # validate date
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise ErrorMessage("Invalid date format. Please use YYYY-MM-DD format.")

        if meal_type.lower() not in MealTypes.values:
            raise InvalidMealType()

        openai_connect = OpenAIConnect()
        response = openai_connect.get_response(description)

        response = json.loads(response)
        response["meal_name"] = meal_name if meal_name else response["meal_name"]
        # serialize into database
        food_serializer = FoodSerializer(data=response)
        if food_serializer.is_valid():
            food_serializer.save()
        else:
            raise ErrorMessage("Error saving food data to database")

        return Response(response)
