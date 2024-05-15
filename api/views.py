from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from dataclasses import dataclass, asdict
from api.openai_connect import OpenAIConnect
from api.models import MealTypes, Food, Meal
import json
from datetime import datetime

from api.serializers import FoodSerializer, MealSerializer

# AUTH

class AuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)

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
    class RequestType:
        """
        For reference only. Not used in the code.
        """
        description: str
        meal_type: str
        date: str or None  # YYYY-MM-DD "2024-05-12"
        meal_name: str or None

    @dataclass
    class ResponseType:
        """
        For reference only. Not used in the code.
        """
        response: str
        follow_up: str
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

    @staticmethod
    def post(request):
        description = request.data.get("description")
        meal_type = request.data.get("meal_type")
        date_str = request.data.get("date")
        meal_name = request.data.get("meal_name")

        temperature = 0.2

        json_format = """
            {
                "response": "your response here. Provide a brief explanation of why you did what you did and any breakdowns of the meal..",
                "follow_up": "Ask a follow up question that would narrow the scope of the response",
                "meal_name":"your meal name here",
                "property1": "value1",
                "property2": "value2",
                "... etc": "..."
            }
        """
        system_prompt = f"""
            You are a nutritionist who is helping a client track their food intake.
            You are an expert at looking at a photo or description of a meal and determining the nutritional content.
            
            """
        openai_connect = OpenAIConnect(system_prompt=system_prompt, temperature=temperature, json_format=json_format)
        system_prompt += f"Include the following information: {openai_connect.properties}"
        # specific params for response

        # DATE STUFF
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ErrorMessage("Invalid date format. Please use YYYY-MM-DD format.")
        else:
            date = datetime.now()

        if meal_type.lower() not in MealTypes.values:
            raise InvalidMealType()



        response = openai_connect.get_response(description)

        response = json.loads(response)
        response["meal_name"] = meal_name if meal_name else response["meal_name"]
        # serialize into database

        food_serializer = FoodSerializer(data=response)
        if food_serializer.is_valid():
            food = food_serializer.save()
        else:
            raise ErrorMessage("Error saving food data to database")

        # find and save meal
        # get food from db

        # meal, created = Meal.objects.get_or_create(meal_type=meal_type, date=date)
        # meal.meal_items.add(food)
        # meal.save()
        # print(meal)

        return Response(response)
