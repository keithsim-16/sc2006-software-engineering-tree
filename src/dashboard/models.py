from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class User(AbstractUser):
	temp = models.CharField(max_length=225)
	init = models.BooleanField(default=True)
	budget_init = models.BooleanField(default=True)

class Transaction(models.Model):
	username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	transaction_type = models.CharField(max_length=225)
	date = models.DateField()
	transaction_name = models.TextField()
	remarks = models.CharField(max_length=225)
	category = models.TextField()
	amount = models.DecimalField(max_digits=20,decimal_places=2)

	def get_absolute_url(self):
		return f"/transactions/{self.id}/"