from django.db import models
import uuid
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # the user's height in centimeters
    height = models.FloatField(default=0)
    # the user's weight in kilograms
    weight = models.FloatField(default=0)
    # the user's age in years
    age = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username + "'s profile"


class Food(models.Model):
    """
    A "food" is a portion or serving of a food or drink that is consumed at a meal or snack.
    For example, a fish and rice dish, a cappuccino, or a slice of bread with butter would all constitute meal items.
    The definition is purposely flexible so that users can track a wide variety of foods and drinks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="")
    # the system with nutritional info is on a *range* of values, so we need to store the min and max values
    # all values are in grams
    calories_min = models.FloatField(default=0)
    calories_max = models.FloatField(default=0)

    protein_min = models.FloatField(default=0)
    protein_max = models.FloatField(default=0)

    total_fat_min = models.FloatField(default=0)
    total_fat_max = models.FloatField(default=0)

    saturated_fat_min = models.FloatField(default=0)
    saturated_fat_max = models.FloatField(default=0)

    carbohydrates_min = models.FloatField(default=0)
    carbohydrates_max = models.FloatField(default=0)

    sugar_min = models.FloatField(default=0)
    sugar_max = models.FloatField(default=0)

    fiber_min = models.FloatField(default=0)
    fiber_max = models.FloatField(default=0)

    cholesterol_min = models.FloatField(default=0)
    cholesterol_max = models.FloatField(default=0)

    sodium_grams_min = models.FloatField(default=0)
    sodium_grams_max = models.FloatField(default=0)

    @staticmethod
    def all_properties() -> list[str]:
        list_of_fields = [field.name for field in Food._meta.get_fields()]
        for field in ["id", "name", "meal"]:
            list_of_fields.remove(field)
        return list_of_fields

    def __str__(self):
        return self.name + " (" + str(self.calories_min) + " - " + str(self.calories_max) + " calories)"


class MealTypes(models.TextChoices):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    OTHER = "other"
    NA = "n/a"

class Meal(models.Model):
    """
    A "meal" is a collection of meal items that are consumed at a specific time.
    For example, a breakfast, lunch, or dinner would all be considered meals.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="")
    meal_items = models.ManyToManyField(Food)
    meal_type = models.CharField(
        max_length=10,
        choices=MealTypes.choices,
        default=MealTypes.NA
    )
    date = models.DateField()
    time = models.TimeField()
    # user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + " (" + str(self.date) + " " + str(self.time) + ")"

    @property
    def total_min_calories(self):
        return sum([meal_item.calories_min for meal_item in self.meal_items.all()])

    @property
    def total_max_calories(self):
        return sum([meal_item.calories_max for meal_item in self.meal_items.all()])

    #... etc. for other nutritional info properties

