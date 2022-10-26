# Import Libraries
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, Transaction, FinancialAccount
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password


# Logged in Views


def home_view(request, *args, **kwargs):
  if request.user.is_authenticated:
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')
    return render(request, "home.html", {})
  else:
    return redirect('Login-page')


def account_view(request, *args, **kwargs):
  # Check if user is logged in
  if request.user.is_authenticated:

    # Check if user has completed initial set-up
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')

    # Add new transaction
    if request.method == "POST":
      if request.POST.get("addNewTrans"):
        username = request.user
        transactionType = request.POST.get("transactionType")
        transactionDate = request.POST.get("transactionDate")
        transactionCategory = request.POST.get("transactionCategory")
        transactionName = request.POST.get("transactionName")
        transactionAmt = request.POST.get("transactionAmt")
        transactionRemarks = request.POST.get("transactionRemarks")

        new_transaction = Transaction.objects.create(username=username, transaction_type=transactionType, date=transactionDate, transaction_name=transactionName,remarks=transactionRemarks,category=transactionCategory,amount=transactionAmt)
        new_transaction.save()

        return redirect('account')

      elif request.POST.get("addNewAcct"):
        username = request.user
        acctType = request.POST.get("acctType")
        acctName = request.POST.get("acctName")
        acctValue = request.POST.get("acctValue")

        new_fa = FinancialAccount.objects.create(username=username, type=acctType, name=acctName, value=acctValue)
        new_fa.save()

        get_user = User.objects.get(username=request.user)
        if acctType == "Assets":
          get_user.net_worth = float(get_user.net_worth) + float(acctValue)
        else:
          get_user.net_worth = float(get_user.net_worth) - float(acctValue)
        get_user.save()

        return redirect('account')
    
    queryset = Transaction.objects.filter(username=request.user).order_by('-date')

    faset = FinancialAccount.objects.filter(username=request.user)
    networth = User.objects.get(username=request.user).net_worth
    if (networth < 0):
      networth = "(" + str(networth * -1) + ")"

    context = {
      "object_list": queryset,
      "fa_list": faset,
      "networth": networth
    }

    return render(request, "account.html", context)
  # If not, back to login page
  else:
    return redirect('Login-page')


def transactions_view(request, *args, **kwargs):
  # Check if user is logged in
  if request.user.is_authenticated:

    # Check if user has completed initial set-up
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')

    queryset = Transaction.objects.filter(username=request.user).order_by('-date')
    
    context = {
      "object_list": queryset
    }

    return render(request, "transactions.html", context)
  # If not, back to login page
  else:
    return redirect('Login-page')


def transaction_lookup_view(request, id):
  # Check if user is logged in
  if request.user.is_authenticated:

    # Check if user has completed initial set-up
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')

    queryset = Transaction.objects.filter(username=request.user).get(id=id)
    
    context = {
      "object_list": queryset
    }

    return render(request, "detailedTransaction.html", context)
  # If not, back to login page
  else:
    return redirect('Login-page')


def setup_view(request, *args, **kwargs):
  if request.user.is_authenticated:
    if request.method == "POST":
      if request.POST.get("completeInit"):
        get_user = User.objects.get(username=request.user)
        get_user.init = False
        get_user.save()
        return redirect('home')

      elif request.POST.get("addNewAcct"):
        username = request.user
        acctType = request.POST.get("acctType")
        acctName = request.POST.get("acctName")
        acctValue = request.POST.get("acctValue")

        new_fa = FinancialAccount.objects.create(username=username, type=acctType, name=acctName, value=acctValue)
        new_fa.save()

        get_user = User.objects.get(username=request.user)
        if acctType == "Assets":
          get_user.net_worth = float(get_user.net_worth) + float(acctValue)
        else:
          get_user.net_worth = float(get_user.net_worth) - float(acctValue)
        get_user.save()

        return redirect('set-up')

    queryset = FinancialAccount.objects.filter(username=request.user)
    networth = User.objects.get(username=request.user).net_worth
    if (networth < 0):
      networth = "(" + str(networth * -1) + ")"

    context = {
      "object_list": queryset,
      "networth": networth
    }
    
    return render(request, "initial.html", context)
  else:
    return redirect('Login-page')


def budget_setup_view(request, *args, **kwargs):
  if request.user.is_authenticated:
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')
    return render(request, "initialBudget.html", {})
  else:
    return redirect('Login-page')


# Account Verification / Creation Views


def Register(request):
  if request.method == "POST":
    Username = request.POST.get("Username")
    FirstName = request.POST.get("firstName")
    LastName = request.POST.get("lastName")
    Email = request.POST.get("email")
    Password1 = request.POST.get("password1")
    Password2 = request.POST.get("password2")

    if Password1 != Password2:
      messages.error(request, "Password are different")
      return redirect('Reg')

    if len(Password1) < 8:
      messages.error(request, "Password too short")
      return redirect('Reg')

    check_username = User.objects.filter(username=Username)
    if check_username:
      messages.error(request, 'Username already exists.')
      return redirect('Reg')

    check_email = User.objects.filter(email=Email)
    if check_email:
      messages.error(request, 'Email already exists.')
      return redirect('Reg')

    new_user = User.objects.create_user(
        username=Username, email=Email, password=Password1)
    new_user.first_name = FirstName
    new_user.last_name = LastName

    new_user.save()

    return redirect('Entering', email=Email)

  return render(request, "register.html", {})


def Login(request):
  if request.method == "POST":
    username = request.POST.get("Username")
    Password = request.POST.get("password")
    Remember = request.POST.get("rememberMe")

    if not Remember:
      request.session.set_expiry(0)

    user = authenticate(username=username, password=Password)
    User_data = User.objects.filter(username=username)

    if user is not None:
      login(request, user)
      get_user = User.objects.get(username=username)
      if get_user.init:
        return redirect('set-up')
      else:
        return redirect('home')
    else:
      if User_data:
        get_user = User.objects.get(username=username)
        if get_user.is_active == False:
          return redirect('Entering', get_user.email)
        else:
          messages.error(request, "Wrong Password Entered.")
          return redirect('Login-page')
      else:
        messages.error(request, "User does not exist.")
        return redirect('Login-page')

  return render(request, 'login.html/', {})


def Logout(request):
  logout(request)
  return redirect('Login-page')


def forget_password(request):
  if request.method == 'POST':
    Email = request.POST['email']
    if User.objects.filter(email=Email):
      return redirect('resetEmail', email=Email) #Password_verification_code
    else:
      messages.error(request, 'User does not exist.')
      return redirect('forgetPW')

  return render(request, "password.html", {})


def password_verification_code(request, email):
  if request.method == 'POST':
    get_user = User.objects.get(email=email)    
    verification = request.POST.get('Verification') 
    check = check_password(verification,get_user.temp)

    if check:
      messages.success(request,"Please reset your password.") 
      return redirect('resetPass',email=email)
    else:
      messages.error(request, "The verification code is wrongly entered.")
      return redirect('enterCode', email=email)

  return render(request, "inputVerificationCode.html")


def reset_page(request, email):
  if request.method == 'POST':
    Password1 = request.POST.get("password1")
    Password2 = request.POST.get("password2")
    if Password1 != Password2:
      messages.error(request, "Password are different")
      return redirect('resetPass', email=email)

    if len(Password1) < 8:
      messages.error(request, "Password too short")
      return redirect('resetPass', email=email)

    get_user = User.objects.get(email=email)
    encryptedpassword = make_password(Password1)
    get_user.password = encryptedpassword
    get_user.save()

    messages.success(request, "Password has been reset.")
    return redirect('Login-page')

  return render(request, "forgotPassword.html")


def input_verification_code(request, email):
  if request.method == 'POST':
    get_user = User.objects.get(email=email)

    verification = request.POST.get('Verification')

    check = check_password(verification, get_user.temp)

    if check:
      get_user.is_active = True 
      get_user.save() #saving the state 
      messages.success(request,"Account activated, proceed to login.") 
      return redirect('Login-page')
    else:
      messages.error(request, "The verification code is wrongly entered.")
      return redirect('Verifying', email=email)

  return render(request, "inputVerificationCode.html")


# Logic Views


def Password_verification_code(request, email):
  get_user = User.objects.get(email=email)
  # get_user.is_active = False
  # get_user.save()

  import random
  random_number = ''
  a = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

  while len(random_number) < 6:
    random_number += random.choice(a)

  # generate a new instance to store the random number
  encryptedpassword = make_password(random_number) 
  get_user.temp = encryptedpassword 
  get_user.save() #save the code into the database with .save()

  print(random_number)
  Email_message = EmailMessage('Reset Password', f'Hi {get_user.get_full_name()}! \n Your verification code is: {random_number}. \n\n Enter this code in our website to activate your account.\n\n In case you have forgotten your username, your username is {get_user.get_username()} If you have any questions, send us an email.\n\n We’re glad you’re here!\n The Tree',
                               settings.EMAIL_HOST_USER,
                               [email]  # recevier
                               )

  Email_message.fail_silently = True
  Email_message.send()
  return redirect('enterCode', email=email) #password_verification_code


def verification_code(request, email):
  get_user = User.objects.get(email=email)
  get_user.is_active = False
  get_user.save()

  import random
  random_number = ''
  a = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

  while len(random_number) < 6:
    random_number += random.choice(a)

  # generate a new instance to store the random number
  encryptedpassword = make_password(random_number) 
  get_user.temp = encryptedpassword 
  get_user.save() #save the code into the database with .save()

  print(random_number)

  Email_message = EmailMessage('Signing up to Tree Application', f'Hi {get_user.get_full_name()}! \n Your verification code is: {random_number}. \n\n Enter this code in our website to activate your account.\n\n If you have any questions, send us an email.\n\n We’re glad you’re here!\n The Tree',
                               settings.EMAIL_HOST_USER,
                               [email]  # recevier
                               )

  Email_message.fail_silently = True
  Email_message.send()
  return redirect('Verifying', email=email)
