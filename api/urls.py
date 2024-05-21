from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from api.views import GetTextResponse, GetMealsAndDetails, GetFoodDetails

urlpatterns = [
    path('get_text_response/', GetTextResponse.as_view(), name='get_text_response'),
    path('token-auth/', obtain_auth_token, name="api_token_auth"),
    path('meals/', GetMealsAndDetails.as_view(), name='get_meal_totals'),
    path('food/<str:id>/', GetFoodDetails.as_view(), name='get_food_details'),
]