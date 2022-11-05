from django.db import models 
from django.contrib.auth.models import AbstractUser 
from django.conf import settings 
 
# Create your models here. 
class User(AbstractUser): 
 temp = models.CharField(max_length=225) 
 init = models.BooleanField(default=True) 
 budget_init = models.BooleanField(default=True) 
 net_worth = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 dividends = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 interest = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 food = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 housing = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 transportation = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 utilities = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 insurance = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 medical = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 personal= models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 recreational = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 miscellaneous = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 leftOver = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 goalPrice = models.DecimalField(max_digits=20,decimal_places=2,default=0) 
 
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
 remarks = models.CharField(max_length=225) 
  
 def get_absolute_urls(self):  
  return f"/budgetFinancial/{self.id}/" 
 
 
class SetAside(models.Model):  
 username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
 category = models.TextField() 
 amount = models.DecimalField(max_digits=20,decimal_places=2) 
 def get_absolute_urlss(self):  
  return f"/setGoals/{self.id}/"