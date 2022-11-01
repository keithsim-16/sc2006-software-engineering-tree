from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class User(AbstractUser):
	temp = models.CharField(max_length=225)
	init = models.BooleanField(default=True)
	budget_init = models.BooleanField(default=True)
	net_worth = models.DecimalField(max_digits=20,decimal_places=2,default=0)

class FinancialAccount(models.Model):
	username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	type = models.CharField(max_length=225)
	name = models.TextField()
	value = models.DecimalField(max_digits=20,decimal_places=2)

	def get_absolute_url(self):
		return f"/account/{self.id}/"

class Transaction(models.Model):
	username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	transaction_acct = models.ForeignKey(FinancialAccount, on_delete=models.CASCADE)
	transaction_type = models.CharField(max_length=225)
	date = models.DateField()
	transaction_name = models.TextField()
	remarks = models.CharField(max_length=225)
	category = models.TextField()
	amount = models.DecimalField(max_digits=20,decimal_places=2)

	def get_absolute_url(self):
		return f"/transactions/{self.id}/"

class Budget(models.Model): 
 username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
 priority = models.CharField(max_length=225) 
 goal_Name = models.CharField(max_length=225) 
 value = models.DecimalField(max_digits=20,decimal_places=2) 
 target_Duration = models.DecimalField(max_digits=20,decimal_places=0) 
 
 def get_absolute_urls(self): 
  return f"/budgetFinancial/{self.id}/"

class History(models.Model):
  username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  date = models.DateField()
  amount = models.DecimalField(max_digits=20,decimal_places=2)

  def get_absolute_url(self):
  	return f"/history/{self.id}/"
