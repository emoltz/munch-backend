from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from api.views import LogFood, GetMealsAndDetails, GetFoodDetails, Apple_CreateAccount, UserExists, \
    Apple_GetUserToken

urlpatterns = [
    path('get-reg-user-token/', obtain_auth_token, name="api_token_auth"),
    path('register-apple/', Apple_CreateAccount.as_view(), name='create_account'),
    path('get-apple-user-token/<str:user_id>/', Apple_GetUserToken.as_view(), name='apple_user_token'),
    path('user-exists/<str:user_id>/', UserExists.as_view(), name='user_exists'),
    path('log-food/', LogFood.as_view(), name='get_text_response'),
    path('meals/', GetMealsAndDetails.as_view(), name='get_meal_info'),
    path('food/<str:id>/', GetFoodDetails.as_view(), name='get_food_details'),
]
