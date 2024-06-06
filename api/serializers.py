from rest_framework import serializers
from .models import Food, Meal, UserProfile, Conversation

class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = '__all__'

class MealSerializer(serializers.ModelSerializer):
    total_min_calories = serializers.SerializerMethodField()
    total_max_calories = serializers.SerializerMethodField()
    total_min_protein = serializers.SerializerMethodField()
    total_max_protein = serializers.SerializerMethodField()
    total_min_total_fat = serializers.SerializerMethodField()
    total_max_total_fat = serializers.SerializerMethodField()
    total_min_saturated_fat = serializers.SerializerMethodField()
    total_max_saturated_fat = serializers.SerializerMethodField()
    total_min_carbohydrates = serializers.SerializerMethodField()
    total_max_carbohydrates = serializers.SerializerMethodField()
    total_min_sugar = serializers.SerializerMethodField()
    total_max_sugar = serializers.SerializerMethodField()
    total_min_fiber = serializers.SerializerMethodField()
    total_max_fiber = serializers.SerializerMethodField()
    total_min_cholesterol = serializers.SerializerMethodField()
    total_max_cholesterol = serializers.SerializerMethodField()
    total_min_sodium_grams = serializers.SerializerMethodField()
    total_max_sodium_grams = serializers.SerializerMethodField()
    # total_min_caffeine = serializers.SerializerMethodField()
    # total_max_caffeine = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = '__all__'

    def get_total_min_calories(self, obj):
        return obj.total_min_calories

    def get_total_max_calories(self, obj):
        return obj.total_max_calories

    def get_total_min_protein(self, obj):
        return obj.total_min_protein

    def get_total_max_protein(self, obj):
        return obj.total_max_protein

    def get_total_min_total_fat(self, obj):
        return obj.total_min_total_fat

    def get_total_max_total_fat(self, obj):
        return obj.total_max_total_fat

    def get_total_min_saturated_fat(self, obj):
        return obj.total_min_saturated_fat

    def get_total_max_saturated_fat(self, obj):
        return obj.total_max_saturated_fat

    def get_total_min_carbohydrates(self, obj):
        return obj.total_min_carbohydrates

    def get_total_max_carbohydrates(self, obj):
        return obj.total_max_carbohydrates

    def get_total_min_sugar(self, obj):
        return obj.total_min_sugar

    def get_total_max_sugar(self, obj):
        return obj.total_max_sugar

    def get_total_min_fiber(self, obj):
        return obj.total_min_fiber

    def get_total_max_fiber(self, obj):
        return obj.total_max_fiber

    def get_total_min_cholesterol(self, obj):
        return obj.total_min_cholesterol

    def get_total_max_cholesterol(self, obj):
        return obj.total_max_cholesterol

    def get_total_min_sodium_grams(self, obj):
        return obj.total_min_sodium_grams

    def get_total_max_sodium_grams(self, obj):
        return obj.total_max_sodium_grams

    # def get_total_min_caffeine(self, obj):
    #     return obj.total_min_caffeine
    #
    # def get_total_max_caffeine(self, obj):
    #     return obj.total_max_caffeine

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'


class CreateUserSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)