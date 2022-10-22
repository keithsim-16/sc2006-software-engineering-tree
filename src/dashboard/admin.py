from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['username', 'transaction_type', 'date', 'transaction_name', 'remarks', 'category', 'amount']
