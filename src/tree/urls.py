"""tree URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from dashboard.views import *

urlpatterns = [
    # Django Admin Page
    path("admin/", admin.site.urls),

    # Logged In Views
    path("set-up/", setup_view, name="set-up"), 
    path("budget-set-up/", budget_setup_view, name="budget-set-up"), 

    path("", home_view, name="home"), 
    path("home/", home_view, name="home"), 
    
    path("account/", account_view, name="account"), 
    path("account/<int:id>/", account_lookup_view, name="detailed_account"), 

    path("transactions/", transactions_view, name="transactions"), 
    path("transactions/<int:id>/", transaction_lookup_view, name="detailed_transaction"), 

    path("budgetFinancial/",budget_view,name="budget"), 
    path("budgetFinancial/<int:id>/",budget_lookup_view,name="detailed_budget"), 
    path("setGoals/",set_goals,name="setGoal"), 

    # Account Verification / Creation Views
    path("registerYourAccount/", Register, name="Reg"), #register acct page
    path('login/', Login, name="Login-page"),
    path("logout/", Logout, name="logout"),
    path("forgot-password/", forget_password, name="forgetPW"), #forget passwd page
    path('verifyingCode/<str:email>/', password_verification_code, name="enterCode"), #for forget passwd
    path('resetPassword/<str:email>',reset_page,name="resetPass"), #change passwd after ^^
    path('verifying/<str:email>/',input_verification_code,name="Verifying"), #for reg acct

    # Logic Views
    path('enteringCode/<str:email>/',verification_code,name="Entering"), 
    path('resetEmail/<str:email>/',Password_verification_code,name="resetEmail"),
]

