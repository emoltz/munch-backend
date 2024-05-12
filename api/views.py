from datetime import datetime

from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from dataclasses import dataclass
from api.openai_connect import OpenAIConnect
from api.models import MealTypes, Food
import json


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
    class Properties:
        meal_name: str
        calories_min: float
        calories_max: float
        protein_min: float
        protein_max: float
        total_fat_min: float
        total_fat_max: float
        saturated_fat_min: float
        saturated_fat_max: float
        carbohydrates_min: float
        carbohydrates_max: float
        sugar_min: float
        sugar_max: float
        fiber_min: float
        fiber_max: float
        cholesterol_min: float
        cholesterol_max: float
        sodium_grams_min: float
        sodium_grams_max: float

    @dataclass
    class RequestArgs:
        prompt: str
        meal_type: str
        date: str  # YYYY-MM-DD "2024-05-12"

    def post(self, request):
        prompt = request.data.get("prompt")
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
        response = openai_connect.get_response(prompt)

        response = json.loads(response)

        # add to db
        date = datetime.strptime(date, "%Y-%m-%d") if date else None
        food = Food.objects.create(
            name=response["meal_name"] if "meal_name" in response else meal_name,
            calories_min=response["calories_min"],
            calories_max=response["calories_max"],
            protein_min=response["protein_min"],
            protein_max=response["protein_max"],
            total_fat_min=response["total_fat_min"],
            total_fat_max=response["total_fat_max"],
            saturated_fat_min=response["saturated_fat_min"],
            saturated_fat_max=response["saturated_fat_max"],
            carbohydrates_min=response["carbohydrates_min"],
            carbohydrates_max=response["carbohydrates_max"],
            sugar_min=response["sugar_min"],
            sugar_max=response["sugar_max"],
            fiber_min=response["fiber_min"],
            fiber_max=response["fiber_max"],
            cholesterol_min=response["cholesterol_min"],
            cholesterol_max=response["cholesterol_max"],
            sodium_grams_min=response["sodium_grams_min"],
            sodium_grams_max=response["sodium_grams_max"],

        )
        food.save()


        return Response(response)
