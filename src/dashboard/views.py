# Import Libraries
from datetime import datetime
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, Transaction, FinancialAccount, Budget
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from dateutil.relativedelta import relativedelta
# Logged in Views


def home_view(request, *args, **kwargs):
  if request.user.is_authenticated:
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')

  
    cashflowdata=[]
    cashflowlabels=[]
    cashflow = [0]*12
    for i in range(12):
      cur_month = Transaction.objects.filter(username=request.user, date__month=datetime.now().month-i)
      cashflowlabels.append([(datetime.now()+ relativedelta(months=-i)).strftime("%b")])
      for j in cur_month:
        if (j.transaction_type == "Income"):
          cashflow[i] += j.amount
        else:
          cashflow[i] -= j.amount
    for k in cashflow:
      cashflowdata.append(float(k))
    
    netWorthdata=[float(User.objects.get(username=request.user).net_worth)-float(cashflow[0])]
    netWorthlabels=[datetime.now().strftime("%b")]
    for i in range(1,12):
      netWorthdata.append(netWorthdata[i-1]-float(cashflow[i]))
      netWorthlabels.append((datetime.now()+ relativedelta(months=-i)).strftime("%b"))
    
  
    
    cashflowlabels.reverse()
    cashflowdata.reverse()
    netWorthdata.reverse()
    netWorthlabels.reverse()
  
  
  
    incomelabels=[]
    incomedata=[]
  
    expenseslabels=[]
    expensesdata=[]
  
  
    
    queryset= Transaction.objects.filter(username=request.user).filter(transaction_type="Income").order_by('amount')
    for transaction in queryset:
      if transaction.category in incomelabels:
        for i in range(len(incomelabels)):
          if transaction.category == incomelabels[i]:
            incomedata[i]=incomedata[i]+float(transaction.amount)
      else:
        incomelabels.append(transaction.category)
        incomedata.append(float(transaction.amount))
    
    queryset= Transaction.objects.filter(username=request.user).filter(transaction_type="Expense").order_by('amount')
    for transaction in queryset:
      if transaction.category in incomelabels:
        for i in range(len(expenseslabels)):
          if transaction.category == expenseslabels[i]:
            expensesdata[i]=expensesdata[i]+float(transaction.amount)
      else:
        expenseslabels.append(transaction.category)
        expensesdata.append(float(transaction.amount))
  
  
    return render(request, "home.html", {'netWorthlabels': netWorthlabels,'netWorthdata': netWorthdata,'cashflowlabels': cashflowlabels,'cashflowdata': cashflowdata,'incomelabels': incomelabels,'incomedata': incomedata,'expenseslabels': expenseslabels,'expensesdata': expensesdata})
  else:
    return redirect('Login-page')


def setup_view(request, *args, **kwargs):
  if request.user.is_authenticated:
    if request.method == "POST":
      if request.POST.get("completeInit"):
        queryset = FinancialAccount.objects.filter(username=request.user)
        if not queryset:
          messages.error(request, "Please add financial accounts.")
          return redirect('set-up')
        else:
          get_user = User.objects.get(username=request.user)
          get_user.init = False
          get_user.save()
          return redirect('home')

      elif request.POST.get("addNewAcct"):
        username = request.user
        acctType = request.POST.get("acctType")
        acctName = request.POST.get("acctName")
        acctValue = request.POST.get("acctValue")

        new_fa = FinancialAccount.objects.create(
            username=username, type=acctType, name=acctName, value=acctValue)
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
        transactionAcct = request.POST.get("transactionAcct")
        transactionDate = request.POST.get("transactionDate")
        transactionCategory = request.POST.get("transactionCategory")
        transactionName = request.POST.get("transactionName")
        transactionAmt = request.POST.get("transactionAmt")
        transactionRemarks = request.POST.get("transactionRemarks")

        get_user = User.objects.get(username=request.user)
        get_fa = FinancialAccount.objects.get(
            name=transactionAcct, username=username)
        if transactionType == "Income":
          get_user.net_worth = float(
              get_user.net_worth) + float(transactionAmt)
          get_fa.value = float(get_fa.value) + float(transactionAmt)
        else:
          get_user.net_worth = float(
              get_user.net_worth) - float(transactionAmt)
          get_fa.value = float(get_fa.value) - float(transactionAmt)

        if get_fa.value < 0:
          messages.error(request, "Insufficient Funds")
          return redirect('account')
        
        get_fa.save()
        get_user.save()

        new_transaction = Transaction.objects.create(username=username, transaction_type=transactionType, transaction_acct=get_fa, date=transactionDate,
                                                     transaction_name=transactionName, remarks=transactionRemarks, category=transactionCategory, amount=transactionAmt)
        new_transaction.save()

        messages.success(request, "Successfully added new transaction.")
        return redirect('account')

      elif request.POST.get("addNewAcct"):
        username = request.user
        acctType = request.POST.get("acctType")
        acctName = request.POST.get("acctName")
        acctValue = request.POST.get("acctValue")

        new_fa = FinancialAccount.objects.create(
            username=username, type=acctType, name=acctName, value=acctValue)
        new_fa.save()

        get_user = User.objects.get(username=request.user)
        if acctType == "Assets":
          get_user.net_worth = float(get_user.net_worth) + float(acctValue)
        else:
          get_user.net_worth = float(get_user.net_worth) - float(acctValue)
        get_user.save()
        
        messages.success(request, "Successfully added new financial account.")
        return redirect('account')

    cur_month = Transaction.objects.filter(username=request.user, date__month=datetime.now().month)

    cashflow = 0

    for i in cur_month:
      if (i.transaction_type == "Income"):
        cashflow += i.amount
      else:
        cashflow -= i.amount

    queryset = Transaction.objects.filter(
        username=request.user).order_by('-date')

    faset = FinancialAccount.objects.filter(
        username=request.user).order_by('-value')
    networth = User.objects.get(username=request.user).net_worth
    if (networth < 0):
      networth = "(" + str(networth * -1) + ")"

    context = {
        "object_list": queryset,
        "fa_list": faset,
        "networth": networth,
        "cashflow": cashflow,
        "currmonth": datetime.now().strftime("%B %Y")
    }

    return render(request, "account.html", context)
  # If not, back to login page
  else:
    return redirect('Login-page')


def account_lookup_view(request, id):
  # Check if user is logged in
  if request.user.is_authenticated:
    if request.method == "POST":
      # Edit Financial Account
      if request.POST.get("editAcct"):
        username = request.user
        FinancialAccounts = FinancialAccount.objects.filter(
            username=username).get(id=id)

        accountType = request.POST.get("acctType")
        accountName = request.POST.get("acctName")
        accountValue = request.POST.get("acctValue")

        get_user = User.objects.get(username=request.user)

        # Update Net Worth According to Edited Financial Account
        if (FinancialAccounts.type != accountType):
          # Asset -> Liability
          if (FinancialAccounts.type == "Assets"):
            get_user.net_worth = float(
                get_user.net_worth) - float(FinancialAccounts.value) - float(accountValue)
          # Liability -> Asset
          elif (FinancialAccounts.type == "Liabilities"):
            get_user.net_worth = float(
                get_user.net_worth) + float(FinancialAccounts.value) + float(accountValue)
        else:
          if (FinancialAccounts.type == "Assets"):
            # Reduce Value of Asset
            if (float(accountValue) < float(FinancialAccounts.value)):
              get_user.net_worth = float(
                  get_user.net_worth) - (float(FinancialAccounts.value) - float(accountValue))
            # Increase Value of Asset
            if (float(accountValue) > float(FinancialAccounts.value)):
              get_user.net_worth = float(
                  get_user.net_worth) + (float(accountValue) - float(FinancialAccounts.value))
          elif (FinancialAccounts.type == "Liabilities"):
            # Reduce Value of Liability
            if (float(accountValue) < float(FinancialAccounts.value)):
              get_user.net_worth = float(
                  get_user.net_worth) + (float(FinancialAccounts.value) - float(accountValue))
            # Increase Value of Liability
            elif (float(accountValue) > float(FinancialAccounts.value)):
              get_user.net_worth = float(
                  get_user.net_worth) - (float(accountValue) - float(FinancialAccounts.value))
        get_user.save()

        FinancialAccounts.type = accountType
        FinancialAccounts.name = accountName
        FinancialAccounts.value = accountValue
        FinancialAccounts.save()
        
        messages.success(request, "Successfully changed financial account details.")
        return redirect('detailed_account', id)

      # Delete Financial Account
      elif request.POST.get("delAcct"):
          FinancialAccounts = FinancialAccount.objects.filter(
              username=request.user).get(id=id)

          get_user = User.objects.get(username=request.user)
          if (FinancialAccounts.type == "Assets"):
            get_user.net_worth = float(
                get_user.net_worth) - float(FinancialAccounts.value)
          else:
            get_user.net_worth = float(
                get_user.net_worth) + float(FinancialAccounts.value)
          get_user.save()

          FinancialAccounts.delete()
          return redirect("account")

    queryset = FinancialAccount.objects.filter(
        username=request.user).get(id=id)

    context = {
        "object_list": queryset
    }

    return render(request, "detailedAccount.html", context)

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

    queryset = Transaction.objects.filter(
        username=request.user).order_by('-date')

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
    if request.method == "POST":
      # Edit transaction
      if request.POST.get("editTrans"):
        username = request.user
        Transactions = Transaction.objects.filter(username=username).get(id=id)

        transactionType = request.POST.get("transactionType")
        transactionAcct = request.POST.get("transactionAcct")
        transactionDate = request.POST.get("transactionDate")
        transactionCategory = request.POST.get("transactionCategory")
        transactionName = request.POST.get("transactionName")
        transactionAmt = request.POST.get("transactionAmt")
        transactionRemarks = request.POST.get("transactionRemarks")

        get_user = User.objects.get(username=username)
        get_fa = FinancialAccount.objects.get(
            name=Transactions.transaction_acct.name, username=username)

        # Update Transaction According to Edited Transaction Details
        # Income -> Expense
        # income 50 become expense 50
        if (Transactions.transaction_type == "Income" and transactionType == "Expense"):
          get_user.net_worth = float(
              get_user.net_worth) - float(Transactions.amount) - float(transactionAmt)
          get_fa.value = float(get_fa.value) - \
              float(Transactions.amount) - float(transactionAmt)
        # Expense -> Income
        elif (Transactions.transaction_type == "Expense" and transactionType == "Income"):
          get_user.net_worth = float(
              get_user.net_worth) + float(Transactions.amount) + float(transactionAmt)
          get_fa.value = float(get_fa.value) + \
              float(Transactions.amount) + float(transactionAmt)
        else:
          # Change Value
          if (Transactions.transaction_type == "Income"):
            get_user.net_worth = float(
                get_user.net_worth) - (float(Transactions.amount) - float(transactionAmt))
            get_fa.value = float(
                get_fa.value) - (float(Transactions.amount) - float(transactionAmt))
          elif (Transactions.transaction_type == "Expense"):
            get_user.net_worth = float(
                get_user.net_worth) + (float(Transactions.amount) - float(transactionAmt))
            get_fa.value = float(
                get_fa.value) + (float(Transactions.amount) - float(transactionAmt))

        if get_fa.value < 0:
          messages.error(request, "Insufficient Funds")
          return redirect('detailed_transaction', id)

        get_user.save()
        get_fa.save()

        Transactions.transaction_type = transactionType
        Transactions.transaction_acct.name = transactionAcct
        Transactions.date = transactionDate
        Transactions.remarks = transactionRemarks
        Transactions.category = transactionCategory
        Transactions.amount = transactionAmt
        Transactions.transaction_name = transactionName
        Transactions.save()

        messages.success(request, "Successfully changed transaction details.")
        return redirect('detailed_transaction', id)

      # Delete Transaction
      elif request.POST.get("delTrans"):
        username = request.user
        Transactions = Transaction.objects.filter(username=username).get(id=id)

        get_user = User.objects.get(username=request.user)
        get_fa = FinancialAccount.objects.get(
            name=Transactions.transaction_acct.name, username=username)

        if Transactions.transaction_type == "Income":
          get_user.net_worth = float(
              get_user.net_worth) - float(Transactions.amount)
          get_fa.value = float(get_fa.value) - float(Transactions.amount)
        else:
          get_user.net_worth = float(
              get_user.net_worth) + float(Transactions.amount)
          get_fa.value = float(get_fa.value) + float(Transactions.amount)
        get_user.save()
        get_fa.save()

        Transactions.delete()
        return redirect("transactions")

    queryset = Transaction.objects.filter(username=request.user).get(id=id)
    faset = FinancialAccount.objects.filter(username=request.user)

    context = {
        "object_list": queryset,
        "fa_list": faset
    }

    return render(request, "detailedTransaction.html", context)

  # If not, back to login page
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


def budget_view(request):
  if request.user.is_authenticated:
    # Add New Goal
    if request.method == "POST":
      username = request.user
      priority = request.POST.get("Priority")
      if priority == "":
        messages.error(request, "..Please enter your priority.")
        return redirect('budget')
      goal_Name = request.POST.get("Goal Name")
      if goal_Name == "":
        messages.error(request, "..Please enter the name of your goal.")
        return redirect('budget')
      value = request.POST.get("Value")
      if value == "":
        messages.error(request, "..Please enter the value of your goal.")
        return redirect('budget')
      target_Duration = request.POST.get("Target Duration")
      if target_Duration == "":
        messages.error(request, "..Please enter the duration of your goal.")
        return redirect('budget')

      new_budget = Budget.objects.create(
          username=username, priority=priority, goal_Name=goal_Name, value=value, target_Duration=target_Duration)
      new_budget.save()

      return redirect('budget')

    queryset = Budget.objects.filter(username=request.user)

    context = {
        "Object_list": queryset
    }
    return render(request, "budgetFinancial.html", context)

  else:
    return redirect('Login-page')


def budget_lookup_view(request, id):
  # Check if user is logged in
  if request.user.is_authenticated:
    # Edit transaction
    if request.method == "POST":
      # Edit Goal Button
      if request.POST.get("editGoal"):
        username = request.user
        budget = Budget.objects.filter(username=username).get(id=id)

        priority = request.POST.get("priority")
        goal_Name = request.POST.get("goal_Name")
        value = request.POST.get("value")
        target_Duration = request.POST.get("target_Duration")

        budget.priority = priority
        budget.goal_Name = goal_Name
        budget.value = value
        budget.target_Duration = target_Duration
        budget.save()

      # Delete Goal
      elif request.POST.get("delGoal"):
        Budgets = Budget.objects.filter(username=request.user).get(id=id)
        Budgets.delete()
        return redirect('budget')

    queryset = Budget.objects.filter(username=request.user).get(id=id)

    context = {
        "Object_list": queryset
    }

    return render(request, "detailedBudget.html", context)

  # If not, back to login page
  else:
    return redirect('Login-page')


def set_goals(request):
  return render(request, "SetGoals.html")


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
      return redirect('resetEmail', email=Email)  # Password_verification_code
    else:
      messages.error(request, 'User does not exist.')
      return redirect('forgetPW')

  return render(request, "password.html", {})


def password_verification_code(request, email):
  if request.method == 'POST':
    get_user = User.objects.get(email=email)
    verification = request.POST.get('Verification')
    check = check_password(verification, get_user.temp)

    if check:
      messages.success(request, "Please reset your password.")
      return redirect('resetPass', email=email)
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
      get_user.save()  # saving the state
      messages.success(request, "Account activated, proceed to login.")
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
  get_user.save()  # save the code into the database with .save()

  print(random_number)
  Email_message = EmailMessage('Reset Password', f'Hi {get_user.get_full_name()}! \n Your verification code is: {random_number}. \n\n Enter this code in our website to activate your account.\n\n In case you have forgotten your username, your username is {get_user.get_username()} If you have any questions, send us an email.\n\n We’re glad you’re here!\n The Tree',
                               settings.EMAIL_HOST_USER,
                               [email]  # recevier
                               )

  Email_message.fail_silently = True
  Email_message.send()
  return redirect('enterCode', email=email)  # password_verification_code


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
  get_user.save()  # save the code into the database with .save()

  print(random_number)

  Email_message = EmailMessage('Signing up to Tree Application', f'Hi {get_user.get_full_name()}! \n Your verification code is: {random_number}. \n\n Enter this code in our website to activate your account.\n\n If you have any questions, send us an email.\n\n We’re glad you’re here!\n The Tree',
                               settings.EMAIL_HOST_USER,
                               [email]  # recevier
                               )

  Email_message.fail_silently = True
  Email_message.send()
  return redirect('Verifying', email=email)
