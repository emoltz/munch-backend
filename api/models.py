from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    name = models.CharField(max_length=255, default="")
    meal_items = models.ManyToManyField(Food)
    meal_type = models.CharField(
        max_length=10,
        choices=MealTypes.choices,
        default=MealTypes.NA
    )
    date = models.CharField(max_length=10, blank=False, null=False) # YYYY-MM-DD "2024-05-12"

    @property
    def total_min_calories(self):
        return sum([meal_item.calories_min for meal_item in self.meal_items.all()])

    @property
    def total_max_calories(self):
        return sum([meal_item.calories_max for meal_item in self.meal_items.all()])

    @property
    def total_min_protein(self):
        return sum([meal_item.protein_min for meal_item in self.meal_items.all()])

    @property
    def total_max_protein(self):
        return sum([meal_item.protein_max for meal_item in self.meal_items.all()])

    @property
    def total_min_total_fat(self):
        return sum([meal_item.total_fat_min for meal_item in self.meal_items.all()])

    @property
    def total_max_total_fat(self):
        return sum([meal_item.total_fat_max for meal_item in self.meal_items.all()])

    @property
    def total_min_saturated_fat(self):
        return sum([meal_item.saturated_fat_min for meal_item in self.meal_items.all()])

    @property
    def total_max_saturated_fat(self):
        return sum([meal_item.saturated_fat_max for meal_item in self.meal_items.all()])

    @property
    def total_min_carbohydrates(self):
        return sum([meal_item.carbohydrates_min for meal_item in self.meal_items.all()])

    @property
    def total_max_carbohydrates(self):
        return sum([meal_item.carbohydrates_max for meal_item in self.meal_items.all()])

    @property
    def total_min_sugar(self):
        return sum([meal_item.sugar_min for meal_item in self.meal_items.all()])

    @property
    def total_max_sugar(self):
        return sum([meal_item.sugar_max for meal_item in self.meal_items.all()])

    @property
    def total_min_fiber(self):
        return sum([meal_item.fiber_min for meal_item in self.meal_items.all()])

    @property
    def total_max_fiber(self):
        return sum([meal_item.fiber_max for meal_item in self.meal_items.all()])

    @property
    def total_min_cholesterol(self):
        return sum([meal_item.cholesterol_min for meal_item in self.meal_items.all()])

    @property
    def total_max_cholesterol(self):
        return sum([meal_item.cholesterol_max for meal_item in self.meal_items.all()])

    @property
    def total_min_sodium_grams(self):
        return sum([meal_item.sodium_grams_min for meal_item in self.meal_items.all()])

    @property
    def total_max_sodium_grams(self):
        return sum([meal_item.sodium_grams_max for meal_item in self.meal_items.all()])

    class Meta:
        unique_together = ["meal_type", "date", "user"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name + " (" + str(self.date) + " " + str(self.meal_type) +  ")"



    #... etc. for other nutritional info properties

class Conversation(models.Model):
    """
    This model tracks any conversation (follow-up questions, etc.) between the user and the bot concerning a specific meal item
    """
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE) # this operates as a conversation id
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.CharField(max_length=100, null=False, blank=False, choices=[("user", "user"), ("bot", "bot")])

# class CurrentThread(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, unique=False, null=False, blank=False)
#     thread_id = models.CharField(max_length=100, null=False, blank=False)
#     date_created = models.DateTimeField(auto_now_add=True)
#
#     @staticmethod
#     def get_current_thread(user: User):
#         # return latest thread
#         return CurrentThread.objects.filter(user=user).last()

# ----------------------
# SIGNALS TO CREATE USER PROFILE
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()