from django.urls import path, include

from api.views import GetTextResponse

urlpatterns = [
    path('get_text_response/', GetTextResponse.as_view(), name='get_text_response'),
]