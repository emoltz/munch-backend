from rest_framework.exceptions import APIException, ParseError, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from dataclasses import dataclass, asdict
from api.openai_connect import OpenAIConnect
from api.models import MealTypes, Food, Meal
import json
from datetime import datetime

from api.serializers import FoodSerializer, MealSerializer

class InvalidMealType(APIException):
    status_code = 400
    default_detail = "Invalid meal type"
    default_code = 'invalid_meal_type'


class ErrorMessage(APIException):
    status_code = 400
    default_detail = "Error processing request."
    default_code = 'error'


class GetTextResponse(APIView):
    permission_classes = [IsAuthenticated]

    @dataclass
    class RequestType:
        """
        For reference only. Not used in the code.
        """
        description: str
        meal_type: str
        date: str or None  # YYYY-MM-DD "2024-05-12"
        name: str or None

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
    def add_food_to_meal(user, food: Food, meal_type: str, date: str, meal_name=None) -> Meal:
        meal, created = Meal.objects.get_or_create(meal_type=meal_type, date=date, user=user)
        meal.meal_items.add(food)
        if meal_name:
            meal.name = meal_name
        meal.save()
        return meal

    def post(self, request):
        user = request.user
        description = request.data.get("description")
        meal_type = request.data.get("meal_type")
        meal_type = meal_type.lower() if meal_type else None
        if not meal_type:
            raise ErrorMessage("Please provide a meal type")

        date_str = request.data.get("date")
        if not date_str:
            raise ErrorMessage("Please provide a date")
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ErrorMessage("Invalid date format. Please use YYYY-MM-DD format.")

        name = request.data.get("name")

        temperature = 0.1

        json_format = """
            {
                "response": "your response here. Provide a brief explanation of why you did what you did and any breakdowns of the meal..",
                "follow_up": "Ask a follow up question that would narrow the scope of the response",
                "name":"your meal name here",
                "property1": "value1",
                "property2": "value2",
                "... etc": "..."
            }
        """
        system_prompt = f"""
            You are a nutritionist who is helping a client track their food intake.
            You are an expert at looking at a photo or description of a meal and determining the nutritional content.
            Because we can't be exact in our estimates, we are providing a minimum and maximum range for each property. 
            The goal is for these values to be as close as possible, but accuracy is the most important, so don't worry too much about the range.
            In order to maximize the accuracy of the estimates, subtract 10% from the minimum and add 10% to the maximum.
            Use these properties: {Food.all_properties()}
            """
        openai_connect = OpenAIConnect(system_prompt=system_prompt, temperature=temperature, json_format=json_format)

        # specific params for response
        if meal_type.lower() not in MealTypes.values:
            raise InvalidMealType()

        response = openai_connect.get_response(description)

        response = json.loads(response)
        response["name"] = name if name else response["name"]
        # serialize into database

        food_serializer = FoodSerializer(data=response)
        if food_serializer.is_valid():
            food = food_serializer.save()
        else:
            raise ErrorMessage("Error saving food data to database")

        self.add_food_to_meal(user, food, meal_type, date_str, name)

        # before returning, add the db id to the response json
        response["db_id"] = food.id

        return Response(response)


class GetFoodDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # return Food[] serialized
        food_id: str = self.kwargs.get('id')
        if not food_id:
            raise ParseError(detail="ID not provided")
        try:
            food = Food.objects.get(id=food_id)
        except Food.DoesNotExist:
            raise NotFound(detail="Food item not found")
        food_serializer = FoodSerializer(food)
        return Response(food_serializer.data)

class GetMealsAndDetails(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        # return Meal[] serialized
        user = request.user
        all_meals = Meal.objects.filter(user=user)
        meal_serializer = MealSerializer(all_meals, many=True)
        return Response(meal_serializer.data)


    @staticmethod
    def post(request):
        user = request.user
        meal = request.data.get("meal_id")
        if not meal:
            raise ErrorMessage("Please provide a meal id")

        # get meal from db
        meal = Meal.objects.get(id=meal)
        if not meal:
            raise ErrorMessage("No meal found with that id for this user")

        # get all foods in meal_items
        meal_items = meal.meal_items.all()

        # now sum all properties
        # calories (min and max)
        total_min_calories = sum([food.calories_min for food in meal_items])
        total_max_calories = sum([food.calories_max for food in meal_items])

        # protein
        total_min_protein = sum([food.protein_min for food in meal_items])
        total_max_protein = sum([food.protein_max for food in meal_items])

        # total fat
        total_min_fat = sum([food.total_fat_min for food in meal_items])
        total_max_fat = sum([food.total_fat_max for food in meal_items])

        # saturated fat
        total_min_sat_fat = sum([food.saturated_fat_min for food in meal_items])
        total_max_sat_fat = sum([food.saturated_fat_max for food in meal_items])

        # carbohydrates
        total_min_carbs = sum([food.carbohydrates_min for food in meal_items])
        total_max_carbs = sum([food.carbohydrates_max for food in meal_items])

        # sugar
        total_min_sugar = sum([food.sugar_min for food in meal_items])
        total_max_sugar = sum([food.sugar_max for food in meal_items])

        # fiber
        total_min_fiber = sum([food.fiber_min for food in meal_items])
        total_max_fiber = sum([food.fiber_max for food in meal_items])

        # cholesterol
        total_min_cholesterol = sum([food.cholesterol_min for food in meal_items])
        total_max_cholesterol = sum([food.cholesterol_max for food in meal_items])

        # sodium_grams
        total_min_sodium_grams = sum([food.sodium_grams_min for food in meal_items])
        total_max_sodium_grams = sum([food.sodium_grams_max for food in meal_items])

        # now return the totals
        response = {
            "meal_name": meal.name,
            "total_min_calories": total_min_calories,
            "total_max_calories": total_max_calories,
            "total_min_protein": total_min_protein,
            "total_max_protein": total_max_protein,
            "total_min_fat": total_min_fat,
            "total_max_fat": total_max_fat,
            "total_min_sat_fat": total_min_sat_fat,
            "total_max_sat_fat": total_max_sat_fat,
            "total_min_carbs": total_min_carbs,
            "total_max_carbs": total_max_carbs,
            "total_min_sugar": total_min_sugar,
            "total_max_sugar": total_max_sugar,
            "total_min_fiber": total_min_fiber,
            "total_max_fiber": total_max_fiber,
            "total_min_cholesterol": total_min_cholesterol,
            "total_max_cholesterol": total_max_cholesterol,
            "total_min_sodium_grams": total_min_sodium_grams,
            "total_max_sodium_grams": total_max_sodium_grams
        }
        return Response(response)


