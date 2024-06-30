from typing import Optional

import requests
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException, ParseError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from dataclasses import dataclass, asdict

from api.firebase_setup import upload_image_to_firebase
from api.openai_connect import OpenAIConnect
from api.models import MealTypes, Food, Meal, UserProfile
import json
from datetime import datetime

from api.serializers import FoodSerializer, MealSerializer, CreateUserSerializer


class InvalidMealType(APIException):
    status_code = 400
    default_detail = "Invalid meal type"
    default_code = 'invalid_meal_type'


class ErrorMessage(APIException):
    status_code = 400
    default_detail = "Error processing request."
    default_code = 'error'


class UserExists(APIView):
    def get(self, request, *args, **kwargs):
        print("Checking if user exists...")
        user_id: str = self.kwargs.get('user_id')
        if not user_id:
            return Response({'message': 'Please provide a user_id'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=user_id).exists():
            return Response({'exists': True}, status=status.HTTP_200_OK)
        return Response({'exists': False}, status=status.HTTP_200_OK)

class SaveFood(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        food_id: str = self.kwargs.get('id')
        if not food_id:
            raise ParseError(detail="ID not provided")
        try:
            food = Food.objects.get(id=food_id)
            food.archived = False
            food.save()
        except Food.DoesNotExist:
            raise NotFound(detail="Food item not found")
        return Response({'message': 'Food item saved successfully.'}, status=status.HTTP_200_OK)


class LogFood(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def add_food_to_meal(user, food: Food, meal_type: str, date: str, meal_name=None) -> Meal:
        meal, created = Meal.objects.get_or_create(meal_type=meal_type, date=date, user=user)
        meal.meal_items.add(food)
        if meal_name:
            meal.name = meal_name

        if not meal.description:
            meal.description = food.initial_description
        else:
            meal.description += " " + food.initial_description
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
        image = request.data.get("image", None)


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
            Use these properties: {Food.properties_to_calculate()}
            """
        openai_connect = OpenAIConnect(system_prompt=system_prompt, temperature=temperature, json_format=json_format)

        # specific params for response
        if meal_type.lower() not in MealTypes.values:
            raise InvalidMealType()

        if image:
            response = openai_connect.get_response(description, base64_image=image)
        else:
            response = openai_connect.get_response(description)

        response = json.loads(response)



        # serialize into database
        # add extra properties
        if image:
            response["image_url"] = openai_connect.image_url
        response["name"] = name if name else response["name"]
        response["archived"] = True
        response["user"] = user.id

        food_serializer = FoodSerializer(data=response)
        if food_serializer.is_valid():
            food = food_serializer.save()
            food.initial_description = description
            food.save()
        else:
            print(food_serializer.errors)
            raise ErrorMessage("Error saving food data to database")

        self.add_food_to_meal(user, food, meal_type, date_str, name)

        # before returning, add the db id to the response json
        response["id"] = food.id

        return Response(response)


class GetFoods(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        user = request.user
        all_foods = Food.objects.filter(user=user)
        food_serializer = FoodSerializer(all_foods, many=True)
        return Response(food_serializer.data)


    @staticmethod
    def post(request):
        user = request.user
        ids_arr: list[str] = request.data.get("ids")
        if not ids_arr:
            raise ErrorMessage("Please provide an array of ids")
        foods = Food.objects.filter(id__in=ids_arr)
        food_serializer = FoodSerializer(foods, many=True)
        return Response(food_serializer.data)


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
        # make sure date is descending
        all_meals = Meal.objects.filter(user=user, date__lte=datetime.now()).order_by('-date')

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


class Apple_GetUserToken(APIView):
    def get(self, request, *args, **kwargs):
        user_id: str = self.kwargs.get('user_id')
        if not user_id:
            return Response({'message': 'Please provide a user_id'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=user_id).exists():
            user = User.objects.get(username=user_id)
            if user.has_usable_password():
                return Response({'message': 'User has a password. Use Sign In endpoint.'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # Ensure user has a token
                if not hasattr(user, 'auth_token'):
                    return Response({'message': 'User does not have a token.'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'token': user.auth_token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'User does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class Apple_CreateAccount(APIView):
    @staticmethod
    def post(request):
        print("Creating Apple User...")
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['user_id']
            email = serializer.validated_data['email']
            first_name = serializer.validated_data.get('first_name', '')
            last_name = serializer.validated_data.get('last_name', '')

            if not User.objects.filter(username=username).exists():
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                user.set_unusable_password()  # As password is not set
                user.save()

                # create token
                Token.objects.create(user=user)

                # TODO Update the UserProfile with additional information
                # user_profile = UserProfile.objects.get(user=user)
                # user_profile.save()

                return Response({'message': 'Apple User registered successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Apple User already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyAppleToken(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        identity_token = request.data.get('identity_token')

        if not user_id or not identity_token:
            return Response({'message': 'Missing user_id or identity_token'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the token with Apple
        client_id = "YOUR_CLIENT_ID"
        client_secret = "YOUR_CLIENT_SECRET"

        response = requests.post(
            'https://appleid.apple.com/auth/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': identity_token,
                'grant_type': 'authorization_code',
            }
        )

        if response.status_code != 200:
            return Response({'message': 'Invalid token'}, status=response.status_code)

        response_data = response.json()
        # TODO: finish this

        # Check if the user exists in the database
        try:
            user = User.objects.get(username=user_id)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the user has a token
        if not hasattr(user, 'auth_token'):
            Token.objects.create(user=user)

        return Response({'token': user.auth_token.key}, status=status.HTTP_200_OK)