from django.db import models
import uuid
from django.contrib.auth.models import User

class Food(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    quantity = models.IntegerField()
    calories = models.FloatField()
    protein = models.FloatField()
    sugars = models.FloatField()
    food_description = models.TextField()

    def __str__(self):
        return self.name


class Meal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    food_items = models.ManyToManyField('Food', blank=True)  # Assuming 'Food' is already defined
    name = models.CharField(max_length=255, default="New Meal")
    date_created = models.DateTimeField(auto_now_add=True)
    date_display = models.CharField(max_length=100)  # This could be generated dynamically in a property
    image_name = models.CharField(max_length=255, default="defaultImage")
    composite_description = models.TextField(blank=True)
    user_description = models.TextField(blank=True)

    @property
    def total_calories(self):
        return sum(food.calories for food in self.food_items.all())

    @property
    def total_protein(self):
        return sum(food.protein for food in self.food_items.all())

    @property
    def total_sugars(self):
        return sum(food.sugars for food in self.food_items.all())

    def compile_composite_description(self):
        self.composite_description = "The following is a description of the entire meal: "
        for food in self.food_items.all():
            self.composite_description += f"{food.food_description}\n"
        self.save()


class Day(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    meals = models.ManyToManyField(Meal, blank=True)

    @property
    def total_calories(self):
        return sum(meal.total_calories for meal in self.meals.all())

    @property
    def total_protein(self):
        return sum(meal.total_protein for meal in self.meals.all())

    @property
    def total_sugars(self):
        return sum(meal.total_sugars for meal in self.meals.all())

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    days = models.ManyToManyField(Day, blank=True)

    @property
    def total_calories(self):
        return sum(day.total_calories for day in self.days.all())

    @property
    def total_protein(self):
        return sum(day.total_protein for day in self.days.all())

    @property
    def total_sugars(self):
        return sum(day.total_sugars for day in self.days.all())