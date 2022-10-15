from django.db import models

# Create your models here.
class generated_code(models.Model):
	code = models.CharField(max_length=225)

class particular_detail(models.Model): 
 Email = models.CharField(max_length=225) 
 Username = models.CharField(max_length=225)