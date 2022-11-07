# Import Libraries
from datetime import datetime
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, Transaction, FinancialAccount, Budget, SetAside
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from dateutil.relativedelta import relativedelta

from .controllers import dataGovAPI

# Logged in Views
def home_view(request, *args, **kwargs):
  if request.user.is_authenticated:
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')

    transactionhistory = Transaction.objects.filter(username=request.user).order_by('date')
    if transactionhistory.exists():
      earliest_month=transactionhistory[0].date
      firstofthismonth=datetime.now().replace(day=1)
      monthstodisplay=1+(firstofthismonth.year - earliest_month.year) * 12 +firstofthismonth.month - earliest_month.month
    else:
      monthstodisplay=1
      
    cashflowdata=[]
    cashflowlabels=[]
    cashflow = [0]*monthstodisplay
    for i in range(monthstodisplay):
      cur_month = Transaction.objects.filter(username=request.user, date__month=datetime.now().month-i)
      cashflowlabels.append((datetime.now() + relativedelta(months=-i)).strftime("%b"))
      for j in cur_month:
        if (j.transaction_type == "Income"):
          cashflow[i] += j.amount
        else:
          cashflow[i] -= j.amount
    for k in cashflow:
      cashflowdata.append(float(k))
   
    netWorthdata=[float(User.objects.get(username=request.user).net_worth)-float(cashflow[0])]
    netWorthlabels=[datetime.now().strftime("%b")]
    for i in range(1,monthstodisplay):
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

        if acctType == None:
          messages.error(request, "Please fill in your account type.")
          return redirect('set-up')

        if acctName == "":
          messages.error(request, "Please fill in your account name.")
          return redirect('set-up')

        if acctValue == "":
          messages.error(request, "Please fill in your account value.")
          return redirect('set-up')


        if not isfloat(acctValue):
          messages.error(request, "Please fill in your account value in decimal number only.")
          return redirect('set-up')

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

        if not isfloat(transactionAmt):
          messages.error(request, "Transaction amount should be a decimal number.")
          return redirect('account')

        if float(transactionAmt) < 0:
          messages.error(request, "Transaction amount should be greater than zero.")
          return redirect('account')



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

        print(acctType)
        if acctType == None:
          messages.error(request, "Please fill in your account type.")
          return redirect('account')

        if acctName == "":
          messages.error(request, "Please fill in your account name.")
          return redirect('account')

        if acctValue == "":
          messages.error(request, "Please fill in your account value.")
          return redirect('account')


        if not isfloat(acctValue):
          messages.error(request, "Please fill in your account value in decimal number only.")
          return redirect('account')

        if float(acctValue) < 0:
          messages.error(request, "Account value should be greater than zero.")
          return redirect('account')

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
    income = 0.0
    expenditure = 0.0
    saved = 0.0
    progress = 0

    for i in cur_month:
      if (i.transaction_type == "Income"):
        cashflow += i.amount
        income += float(i.amount)
      else:
        cashflow -= i.amount
        expenditure += float(i.amount)

    b = Budget.objects.filter(username=request.user)
    for instance in b:
      income -= float(instance.per_month)
      saved += float(instance.per_month)
      break
    else:
      income /= 2
      saved = income

    if income > 0:
      progress = round((expenditure / income) * 100, 2)

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
        "currmonth": datetime.now().strftime("%B %Y"),
        "income": income,
        "progress": progress,
        "expenditure": expenditure,
        "saved": saved
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

        if accountType == None:
          messages.error(request, "Please fill in your account type.")
          return redirect('set-up')

        if accountName == "":
          messages.error(request, "Please fill in your account name.")
          return redirect('set-up')

        if accountValue == "":
          messages.error(request, "Please fill in your account value.")
          return redirect('set-up')

        if not isfloat(accountValue):
          messages.error(request, "Please fill in your account value in decimal number only.")
          return redirect('set-up')

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

        if not isfloat(transactionAmt):
          messages.error(request, "Please fill in your transaction value in decimal number only.")
          return redirect('detailed_transaction',id=id)

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
    if request.method == "POST":
      if request.POST.get("completeBudgetInit"):
        queryset = Budget.objects.filter(username=request.user)
        if not queryset:
          messages.error(request, "Please add budget.")
          return redirect('budget-set-up')
        else:
          get_user = User.objects.get(username=request.user)
          get_user.budget_init = False
          get_user.save()
          return redirect('setGoal')

    if request.method == "POST":
      username = request.user
      priority = request.POST.get("Priority")
      if priority == "":
        messages.error(request, "Please enter your priority.")
        return redirect('budget')
      goal_Name = request.POST.get("Goal Name")
      if goal_Name == "":
        messages.error(request, "Please enter the name of your goal.")
        return redirect('budget')
      value = request.POST.get("Value")
      if value == "":
        messages.error(request, "Please enter the value of your goal.")
        return redirect('budget')
      target_Duration = request.POST.get("Target Duration")
      if target_Duration == "":
        messages.error(request, "Please enter the duration of your goal.")
        return redirect('budget')

      if not isfloat(value):
        messages.error(request, "Please fill in your goal value in decimal number only.")
        return redirect('budget-set-up')

      if target_Duration.isdigit() == False:
        messages.error(request, "Please enter in the target duration in integer only.")
        return redirect('budget')

      get_user.leftOver = float(get_user.net_worth) - float(get_user.dividends) - float(get_user.interest) - float(get_user.food) - float(get_user.housing) - float(get_user.transportation) - float(get_user.utilities)- float(get_user.insurance) - float(get_user.medical) - float(get_user.personal)- float(get_user.recreational) - float(get_user.miscellaneous)

      get_user.goalPrice = float(value)/float(target_Duration)


      if get_user.leftOver/30 < get_user.goalPrice:
        remarks = "It is not possible to achieve this goal, please delete this goal and choose wisely"
      else:
        remarks = "You must save up $" + str(round(get_user.goalPrice*30,2)) + " per month or $" + str(round(get_user.goalPrice,2)) + " per day."
      
      new_budget = Budget.objects.create(
          username=username, priority=priority, goal_Name=goal_Name, value=value, target_Duration=target_Duration,remarks = remarks, per_month=round(get_user.goalPrice*30,2))
      new_budget.save()

      username = request.user
      food_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      housing_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      transportation_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      utilities_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      insurance_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      medical_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      personal_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      recreational_list = [0,0,0,0,0,0,0,0,0,0,0,0]
      miscellaneous_list = [0,0,0,0,0,0,0,0,0,0,0,0]

      count=0
      hcount=0
      tcount=0
      ucount=0
      icount=0
      mcount=0
      pcount=0
      rcount=0
      micount=0

      if request.user.is_authenticated:
        q = Transaction.objects.filter(username=request.user)
        for instance in q:
          if instance.date.month == 1 and instance.category == "Food":
            food_list[0]= food_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Food":
            food_list[1]= food_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Food":
            food_list[2]= food_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Food":
            food_list[3]= food_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Food":
            food_list[4]= food_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Food":
            food_list[5]= food_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Food":
            food_list[6]= food_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Food":
            food_list[7]= food_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Food":
            food_list[8]= food_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Food":
            food_list[9]= food_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Food":
            food_list[10]= food_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Food":
            food_list[11]= food_list[11] + instance.amount 


          # amount for housing
          if instance.date.month == 1 and instance.category == "Housing":
            housing_list[0]= housing_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Housing":
            housing_list[1]= housing_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Housing":
            housing_list[2]= housing_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Housing":
            housing_list[3]= housing_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Housing":
            housing_list[4]= housing_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Housing":
            housing_list[5]= housing_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Housing":
            housing_list[6]= housing_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Housing":
            housing_list[7]= housing_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Housing":
            housing_list[8]= housing_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Housing":
            housing_list[9]= housing_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Housing":
            housing_list[10]= housing_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Housing":
            housing_list[11]= housing_list[11] + instance.amount 

          # amount for transportation
          if instance.date.month == 1 and instance.category == "Transportation":
            transportation_list[0]= transportation_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Transportation":
            transportation_list[1]= transportation_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Transportation":
            transportation_list[2]= transportation_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Transportation":
            transportation_list[3]= transportation_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Transportation":
            transportation_list[4]= transportation_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Transportation":
            transportation_list[5]= transportation_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Transportation":
            transportation_list[6]= transportation_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Transportation":
            transportation_list[7]= transportation_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Transportation":
            transportation_list[8]= transportation_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Transportation":
            transportation_list[9]= transportation_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Transportation":
            transportation_list[10]= transportation_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Transportation":
            transportation_list[11]= transportation_list[11] + instance.amount 

          # amount for utilities
          if instance.date.month == 1 and instance.category == "Utilities":
            utilities_list[0]= utilities_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Utilities":
            utilities_list[1]= utilities_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Utilities":
            utilities_list[2]= utilities_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Utilities":
            utilities_list[3]= utilities_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Utilities":
            utilities_list[4]= utilities_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Utilities":
            utilities_list[5]= utilities_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Utilities":
            utilities_list[6]= utilities_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Utilities":
            utilities_list[7]= utilities_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Utilities":
            utilities_list[8]= utilities_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Utilities":
            utilities_list[9]= utilities_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Utilities":
            utilities_list[10]= utilities_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Utilities":
            utilities_list[11]= utilities_list[11] + instance.amount 

          # amount for insurance
          if instance.date.month == 1 and instance.category == "Insurance":
            insurance_list[0]= insurance_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Insurance":
            insurance_list[1]= insurance_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Insurance":
            insurance_list[2]= insurance_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Insurance":
            insurance_list[3]= insurance_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Insurance":
            insurance_list[4]= insurance_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Insurance":
            insurance_list[5]= insurance_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Insurance":
            insurance_list[6]= insurance_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Insurance":
            insurance_list[7]= insurance_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Insurance":
            insurance_list[8]= insurance_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Insurance":
            insurance_list[9]= insurance_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Insurance":
            insurance_list[10]= insurance_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Insurance":
            insurance_list[11]= insurance_list[11] + instance.amount
        

          # amount for medical
          if instance.date.month == 1 and instance.category == "Medical":
            medical_list[0]= medical_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Medical":
            medical_list[1]= medical_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Medical":
            medical_list[2]= medical_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Medical":
            medical_list[3]= medical_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Medical":
            medical_list[4]= medical_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Medical":
            medical_list[5]= medical_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Medical":
            medical_list[6]= medical_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Medical":
            medical_list[7]= medical_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Medical":
            medical_list[8]= medical_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Medical":
            medical_list[9]= medical_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Medical":
            medical_list[10]= medical_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Medical":
            medical_list[11]= medical_list[11] + instance.amount


          # amount for personal
          if instance.date.month == 1 and instance.category == "Personal":
            personal_list[0]= personal_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Personal":
            personal_list[1]= personal_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Personal":
            personal_list[2]= personal_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Personal":
            personal_list[3]= personal_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Personal":
            personal_list[4]= personal_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Personal":
            personal_list[5]= personal_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Personal":
            personal_list[6]= personal_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Personal":
            personal_list[7]= personal_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Personal":
            personal_list[8]= personal_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Personal":
            personal_list[9]= personal_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Personal":
            personal_list[10]= personal_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Personal":
            personal_list[11]= personal_list[11] + instance.amount


          # amount for recreational
          if instance.date.month == 1 and instance.category == "Recreational":
            recreational_list[0]= recreational_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Recreational":
            recreational_list[1]= recreational_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Recreational":
            recreational_list[2]= recreational_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Recreational":
            recreational_list[3]= recreational_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Recreational":
            recreational_list[4]= recreational_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Recreational":
            recreational_list[5]= recreational_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Recreational":
            recreational_list[6]= recreational_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Recreational":
            recreational_list[7]= recreational_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Recreational":
            recreational_list[8]= recreational_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Recreational":
            recreational_list[9]= recreational_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Recreational":
            recreational_list[10]= recreational_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Recreational":
            recreational_list[11]= recreational_list[11] + instance.amount


          # amount for miscellaneous
          if instance.date.month == 1 and instance.category == "Miscellaneous":
            miscellaneous_list[0]= miscellaneous_list[0] + instance.amount 

          if instance.date.month == 2 and instance.category == "Miscellaneous":
            miscellaneous_list[1]= miscellaneous_list[1] + instance.amount 

          if instance.date.month == 3 and instance.category == "Miscellaneous":
            miscellaneous_list[2]= miscellaneous_list[2] + instance.amount 

          if instance.date.month == 4 and instance.category == "Miscellaneous":
            miscellaneous_list[3]= miscellaneous_list[3] + instance.amount 

          if instance.date.month == 5 and instance.category == "Miscellaneous":
            miscellaneous_list[4]= miscellaneous_list[4] + instance.amount 

          if instance.date.month == 6 and instance.category == "Miscellaneous":
            miscellaneous_list[5]= miscellaneous_list[5] + instance.amount 

          if instance.date.month == 7 and instance.category == "Miscellaneous":
            miscellaneous_list[6]= miscellaneous_list[6] + instance.amount 

          if instance.date.month == 8 and instance.category == "Miscellaneous":
            miscellaneous_list[7]= miscellaneous_list[7] + instance.amount 

          if instance.date.month == 9 and instance.category == "Miscellaneous":
            miscellaneous_list[8]= miscellaneous_list[8] + instance.amount 

          if instance.date.month == 10 and instance.category == "Miscellaneous":
            miscellaneous_list[9]= miscellaneous_list[9] + instance.amount 

          if instance.date.month == 11 and instance.category == "Miscellaneous":
            miscellaneous_list[10]= miscellaneous_list[10] + instance.amount 

          if instance.date.month == 12 and instance.category == "Miscellaneous":
            miscellaneous_list[11]= miscellaneous_list[11] + instance.amount


        for i in food_list:
          if i != 0:
            count=count+1

        for i in housing_list:
          if i != 0:
            hcount=hcount+1

        for i in transportation_list:
          if i != 0:
            tcount=tcount+1

        for i in utilities_list:
          if i != 0:
            ucount=ucount+1

        for i in insurance_list:
          if i != 0:
            icount=icount+1

        for i in medical_list:
          if i != 0:
            mcount=mcount+1

        for i in personal_list:
          if i != 0:
            pcount=pcount+1

        for i in recreational_list:
          if i != 0:
            rcount=rcount+1

        for i in miscellaneous_list:
          if i != 0:
            micount=micount+1

        sumFood=0
        sumHousing=0
        sumTransportation=0
        sumUtilities=0
        sumInsurance=0
        sumMedical=0
        sumPersonal=0
        sumRecreational=0
        sumMiscellaneous=0

        avgFood=0
        avgHousing=0
        avgTransportation=0
        avgUtilities=0
        avgInsurance=0
        avgMedical=0
        avgPersonal=0
        avgRecreational=0
        avgMiscellaneous=0

        for i in food_list:
          sumFood=sumFood+i

        for i in housing_list:
          sumHousing=sumHousing+i

        for i in transportation_list:
          sumTransportation=sumTransportation+i

        for i in utilities_list:
          sumUtilities=sumUtilities+i

        for i in insurance_list:
          sumInsurance=sumInsurance+i

        for i in medical_list:
          sumMedical=sumMedical+i

        for i in personal_list:
          sumPersonal=sumPersonal+i

        for i in recreational_list:
          sumRecreational=sumRecreational+i

        for i in miscellaneous_list:
          sumMiscellaneous=sumMiscellaneous+i

        if count ==0:
          avgFood = sumFood/1
        else:
          avgFood = sumFood/count
        if hcount ==0:
          avgHousing = sumHousing/1
        else:
          avgHousing = sumHousing/hcount
        if tcount == 0:
          avgTransportation = sumTransportation/1
        else:
          avgTransportation = sumTransportation/tcount
        if ucount == 0:
          avgUtilities = sumUtilities/1
        else:  
          avgUtilities = sumUtilities/ucount
        if icount == 0:
          avgInsurance = sumInsurance/1
        else:
          avgInsurance = sumInsurance/icount
        if mcount ==0:
          avgMedical = sumMedical/1
        else:
          avgMedical = sumMedical/mcount
        if pcount ==0:
          avgPersonal = sumPersonal/1
        else:
          avgPersonal = sumPersonal/pcount
        if rcount ==0:
          avgRecreational = sumRecreational/1
        else:
          avgRecreational = sumRecreational/rcount
        if micount == 0:
          avgMiscellaneous = sumMiscellaneous/1
        else:
          avgMiscellaneous = sumMiscellaneous/micount

        queryset = SetAside.objects.filter(username=request.user)
        queryset.delete()

        new_setAside = SetAside.objects.create(username=username, category="Food",amount=avgFood)
        
        new_setAside = SetAside.objects.create(username=username, category="Housing",amount=avgHousing)
        
        new_setAside = SetAside.objects.create(username=username, category="Transportation",amount=avgTransportation)
        
        new_setAside = SetAside.objects.create(username=username, category="Utilities",amount=avgUtilities)
        
        new_setAside = SetAside.objects.create(username=username, category="Insurance",amount=avgInsurance)
        
        new_setAside = SetAside.objects.create(username=username, category="Medical",amount=avgMedical)
       
        new_setAside = SetAside.objects.create(username=username, category="Personal",amount=avgPersonal)
        
        new_setAside = SetAside.objects.create(username=username, category="Recreational",amount=avgRecreational)
        
        new_setAside = SetAside.objects.create(username=username, category="Miscellaneous",amount=avgMiscellaneous)
        new_setAside.save()

      return redirect('budget')

    queryset = Budget.objects.filter(username=request.user)

    context = {
        "Object_list": queryset
    }
    return render(request, "budgetFinancial.html", context)
  else:
    return redirect('Login-page')


def budget_view(request):
  if request.user.is_authenticated:
    get_user = User.objects.get(username=request.user)
    if get_user.init:
      return redirect('set-up')

    if get_user.budget_init:
      return redirect('budget-set-up')

    return redirect('setGoal')

  else:
    return redirect('Login-page')


def budget_lookup_view(request, id):
  # Check if user is logged in
  if request.user.is_authenticated:
    # Edit transaction
    get_user = User.objects.get(username=request.user)
    if request.method == "POST":
      # Edit Goal Button
      if request.POST.get("editGoal"):
        username = request.user
        budget = Budget.objects.filter(username=username).get(id=id)

        priority = request.POST.get("priority")
        goal_Name = request.POST.get("goal_Name")
        value = request.POST.get("value")
        target_Duration = request.POST.get("target_Duration")

        if not isfloat(value):
          messages.error(request, "Please fill in your goal value in decimal number only.")
          return redirect('detailed_budget',id=id)

        if not target_Duration.isdigit():
          messages.error(request, "Please fill in your target duration in whole number only.")
          return redirect('detailed_budget',id=id)

        budget.priority = priority
        budget.goal_Name = goal_Name
        budget.value = value
        budget.target_Duration = target_Duration
        budget.save()

        get_user.leftOver = float(get_user.net_worth)

        get_user.goalPrice = float(value)/float(target_Duration)


        if get_user.leftOver/30 < get_user.goalPrice:
          remarks = "It is not possible to achieve this goal, please delete this goal and choose wisely"
        else:
          remarks = "You must save up $" + str(round(get_user.goalPrice*30,2)) + " per month or $" + str(round(get_user.goalPrice,2)) + " per day."
            
        new_budget = Budget.objects.get(username=username)
        new_budget.remarks = remarks
        new_budget.save()

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


def set_aside_view(request,id):
  # Check if user is logged in
  if request.user.is_authenticated:
    # Edit transaction
    if request.method == "POST":
      get_user = User.objects.get(username=request.user)
      # Edit Goal Button
      if request.POST.get("editSetAside"):
        username = request.user
        setAside = SetAside.objects.filter(username=username).get(id=id)

        setCat = request.POST.get("SetCategory")
        setAmount = request.POST.get("SetAmt")

        if not isfloat(setAmount):
          messages.error(request, "Please fill in your amount in decimal number only.")
          return redirect('setAside')

        if setAside.category == setCat:
          if setCat =='Dividends':
              get_user.dividends = float(get_user.dividends) - float(setAside.amount)
              get_user.dividends = float(get_user.dividends) + float(setAmount)
              get_user.save()

          if setCat == 'Interest':
              get_user.interest = float(get_user.interest) - float(setAside.amount)
              get_user.interest = float(get_user.interest) + float(setAmount)
              get_user.save()
                
          if setCat =='Food':
              get_user.food = float(get_user.food) - float(setAside.amount)
              get_user.food = float(get_user.food) + float(setAmount)
              get_user.save()

          if setCat == 'Housing':
              get_user.housing = float(get_user.housing) - float(setAside.amount)
              get_user.housing = float(get_user.housing) + float(setAmount)
              get_user.save()

          if setCat =='Transportation':
              get_user.transportation = float(get_user.transportation) - float(setAside.amount)
              get_user.transportation = float(get_user.transportation) + float(setAmount)
              get_user.save()

          if setCat == 'Utilities':
              get_user.utilities = float(get_user.utilities) - float(setAside.amount)
              get_user.utilities = float(get_user.utilities) + float(setAmount)
              get_user.save()
                
          if setCat =='Insurance':
              get_user.insurance = float(get_user.insurance) - float(setAside.amount)
              get_user.insurance = float(get_user.insurance) + float(setAmount)
              get_user.save()

          if setCat == 'Medical':
              get_user.medical = float(get_user.medical) - float(setAside.amount)
              get_user.medical = float(get_user.medical) + float(setAmount)
              get_user.save()

          if setCat == 'Personal':
              get_user.personal = float(get_user.personal) - float(setAside.amount)
              get_user.personal = float(get_user.personal) + float(setAmount)
              get_user.save()
                
          if setCat =='Recreational':
              get_user.recreational = float(get_user.recreational) - float(setAside.amount)
              get_user.recreational = float(get_user.recreational) + float(setAmount)
              get_user.save()

          if setCat == 'Miscellaneous':
              get_user.miscellaneous = float(get_user.miscellaneous) - float(setAside.amount)
              get_user.miscellaneous = float(get_user.miscellaneous) + float(setAmount)
              get_user.save()
        else:
          if setAside.category =='Dividends':
              get_user.dividends = float(get_user.dividends) - float(setAside.amount)
              get_user.save()

          if setCat =='Dividends':
              get_user.dividends = float(get_user.dividends) + float(setAmount)
              get_user.save()

          if setAside.category == 'Interest':
              get_user.interest = float(get_user.interest) - float(setAside.amount)
              get_user.save()

          if setCat == 'Interest':
              get_user.interest = float(get_user.interest) + float(setAmount)
              get_user.save()

          if setAside.category =='Food':
              get_user.food = float(get_user.food) - float(setAside.amount)
              get_user.save()

          if setCat =='Food':
              get_user.food = float(get_user.food) + float(setAmount)
              get_user.save()

          if setAside.category == 'Housing':
              get_user.housing = float(get_user.housing) - float(setAside.amount)
              get_user.save()

          if setCat == 'Housing':
              get_user.housing = float(get_user.housing) + float(setAmount)
              get_user.save()

          if setAside.category == 'Transportation':
              get_user.transportation = float(get_user.transportation) - float(setAside.amount)
              get_user.save()

          if setCat == 'Transportation':
              get_user.transportation = float(get_user.transportation) + float(setAmount)
              get_user.save()

          if setAside.category == 'Utilities':
              get_user.utilities = float(get_user.utilities) - float(setAside.amount)
              get_user.save()

          if setCat == 'Utilities':
              get_user.utilities = float(get_user.utilities) + float(setAmount)
              get_user.save()

          if setAside.category == 'Insurance':
              get_user.insurance = float(get_user.insurance) - float(setAside.amount)
              get_user.save()

          if setCat == 'Insurance':
              get_user.insurance = float(get_user.insurance) + float(setAmount)
              get_user.save()

          if setAside.category == 'Medical':
              get_user.medical = float(get_user.medical) - float(setAside.amount)
              get_user.save()

          if setCat == 'Medical':
              get_user.medical = float(get_user.medical) + float(setAmount)
              get_user.save()

          if setAside.category == 'Personal':
              get_user.personal = float(get_user.personal) - float(setAside.amount)
              get_user.save()

          if setCat == 'Personal':
              get_user.personal = float(get_user.personal) + float(setAmount)
              get_user.save()

          if setAside.category == 'Recreational':
              get_user.recreational = float(get_user.recreational) - float(setAside.amount)
              get_user.save()

          if setCat == 'Recreational':
              get_user.recreational = float(get_user.recreational) + float(setAmount)
              get_user.save()

          if setAside.category == 'Miscellaneous':
              get_user.miscellaneous = float(get_user.miscellaneous) - float(setAside.amount)
              get_user.save()

          if setCat == 'Miscellaneous':
              get_user.miscellaneous = float(get_user.miscellaneous) + float(setAmount)
              get_user.save()


        setAside.category=setCat
        setAside.amount=setAmount
        
        setAside.save()

      # Delete Goal
      elif request.POST.get("delSetAside"):
        setAside = SetAside.objects.filter(username=request.user).get(id=id)

        if setAside.category =='Dividends':
            get_user.dividends = float(get_user.dividends) - float(setAside.amount)
            get_user.save()

        if setAside.category == 'Interest':
            get_user.interest = float(get_user.interest) - float(setAside.amount)
            get_user.save()
              
        if setAside.category =='Food':
            get_user.food = float(get_user.food) - float(setAside.amount)
            get_user.save()

        if setAside.category == 'Housing':
            get_user.housing = float(get_user.housing) - float(setAside.amount)
            get_user.save()

        if setAside.category =='Transportation':
            get_user.transportation = float(get_user.transportation) - float(setAside.amount)
            get_user.save()

        if setAside.category == 'Utilities':
            get_user.utilities = float(get_user.utilities) - float(setAside.amount)
            get_user.save()
              
        if setAside.category =='Insurance':
            get_user.insurance = float(get_user.insurance) - float(setAside.amount)
            get_user.save()

        if setAside.category == 'Medical':
            get_user.medical = float(get_user.medical) - float(setAside.amount)
            get_user.save()

        if setAside.category == 'Personal':
            get_user.personal = float(get_user.personal) - float(setAside.amount)
            get_user.save()
              
        if setAside.category =='Recreational':
            get_user.recreational = float(get_user.recreational) - float(setAside.amount)
            get_user.save()

        if setAside.category == 'Miscellaneous':
            get_user.miscellaneous = float(get_user.miscellaneous) - float(setAside.amount)
            get_user.save()

        setAside.delete()
        return redirect('setGoal')

    queryset = SetAside.objects.filter(username=request.user).get(id=id)

    context = {
        "Object_list": queryset
    }

    return render(request, "detailedSetAside.html", context)

  # If not, back to login page
  else:
    return redirect('Login-page')


def set_goals(request):
  username = request.user
  food_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  housing_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  transportation_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  utilities_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  insurance_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  medical_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  personal_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  recreational_list = [0,0,0,0,0,0,0,0,0,0,0,0]
  miscellaneous_list = [0,0,0,0,0,0,0,0,0,0,0,0]

  count=0
  hcount=0
  tcount=0
  ucount=0
  icount=0
  mcount=0
  pcount=0
  rcount=0
  micount=0

  if request.user.is_authenticated:
    q = Transaction.objects.filter(username=request.user)
    for instance in q:
      if instance.date.month == 1 and instance.category == "Food":
        food_list[0]= food_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Food":
        food_list[1]= food_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Food":
        food_list[2]= food_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Food":
        food_list[3]= food_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Food":
        food_list[4]= food_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Food":
        food_list[5]= food_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Food":
        food_list[6]= food_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Food":
        food_list[7]= food_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Food":
        food_list[8]= food_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Food":
        food_list[9]= food_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Food":
        food_list[10]= food_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Food":
        food_list[11]= food_list[11] + instance.amount 


      # amount for housing
      if instance.date.month == 1 and instance.category == "Housing":
        housing_list[0]= housing_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Housing":
        housing_list[1]= housing_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Housing":
        housing_list[2]= housing_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Housing":
        housing_list[3]= housing_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Housing":
        housing_list[4]= housing_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Housing":
        housing_list[5]= housing_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Housing":
        housing_list[6]= housing_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Housing":
        housing_list[7]= housing_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Housing":
        housing_list[8]= housing_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Housing":
        housing_list[9]= housing_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Housing":
        housing_list[10]= housing_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Housing":
        housing_list[11]= housing_list[11] + instance.amount 

      # amount for transportation
      if instance.date.month == 1 and instance.category == "Transportation":
        transportation_list[0]= transportation_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Transportation":
        transportation_list[1]= transportation_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Transportation":
        transportation_list[2]= transportation_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Transportation":
        transportation_list[3]= transportation_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Transportation":
        transportation_list[4]= transportation_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Transportation":
        transportation_list[5]= transportation_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Transportation":
        transportation_list[6]= transportation_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Transportation":
        transportation_list[7]= transportation_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Transportation":
        transportation_list[8]= transportation_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Transportation":
        transportation_list[9]= transportation_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Transportation":
        transportation_list[10]= transportation_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Transportation":
        transportation_list[11]= transportation_list[11] + instance.amount 

      # amount for utilities
      if instance.date.month == 1 and instance.category == "Utilities":
        utilities_list[0]= utilities_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Utilities":
        utilities_list[1]= utilities_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Utilities":
        utilities_list[2]= utilities_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Utilities":
        utilities_list[3]= utilities_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Utilities":
        utilities_list[4]= utilities_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Utilities":
        utilities_list[5]= utilities_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Utilities":
        utilities_list[6]= utilities_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Utilities":
        utilities_list[7]= utilities_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Utilities":
        utilities_list[8]= utilities_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Utilities":
        utilities_list[9]= utilities_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Utilities":
        utilities_list[10]= utilities_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Utilities":
        utilities_list[11]= utilities_list[11] + instance.amount 

      # amount for insurance
      if instance.date.month == 1 and instance.category == "Insurance":
        insurance_list[0]= insurance_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Insurance":
        insurance_list[1]= insurance_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Insurance":
        insurance_list[2]= insurance_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Insurance":
        insurance_list[3]= insurance_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Insurance":
        insurance_list[4]= insurance_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Insurance":
        insurance_list[5]= insurance_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Insurance":
        insurance_list[6]= insurance_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Insurance":
        insurance_list[7]= insurance_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Insurance":
        insurance_list[8]= insurance_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Insurance":
        insurance_list[9]= insurance_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Insurance":
        insurance_list[10]= insurance_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Insurance":
        insurance_list[11]= insurance_list[11] + instance.amount
    

      # amount for medical
      if instance.date.month == 1 and instance.category == "Medical":
        medical_list[0]= medical_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Medical":
        medical_list[1]= medical_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Medical":
        medical_list[2]= medical_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Medical":
        medical_list[3]= medical_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Medical":
        medical_list[4]= medical_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Medical":
        medical_list[5]= medical_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Medical":
        medical_list[6]= medical_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Medical":
        medical_list[7]= medical_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Medical":
        medical_list[8]= medical_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Medical":
        medical_list[9]= medical_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Medical":
        medical_list[10]= medical_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Medical":
        medical_list[11]= medical_list[11] + instance.amount


      # amount for personal
      if instance.date.month == 1 and instance.category == "Personal":
        personal_list[0]= personal_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Personal":
        personal_list[1]= personal_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Personal":
        personal_list[2]= personal_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Personal":
        personal_list[3]= personal_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Personal":
        personal_list[4]= personal_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Personal":
        personal_list[5]= personal_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Personal":
        personal_list[6]= personal_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Personal":
        personal_list[7]= personal_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Personal":
        personal_list[8]= personal_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Personal":
        personal_list[9]= personal_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Personal":
        personal_list[10]= personal_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Personal":
        personal_list[11]= personal_list[11] + instance.amount


      # amount for recreational
      if instance.date.month == 1 and instance.category == "Recreational":
        recreational_list[0]= recreational_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Recreational":
        recreational_list[1]= recreational_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Recreational":
        recreational_list[2]= recreational_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Recreational":
        recreational_list[3]= recreational_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Recreational":
        recreational_list[4]= recreational_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Recreational":
        recreational_list[5]= recreational_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Recreational":
        recreational_list[6]= recreational_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Recreational":
        recreational_list[7]= recreational_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Recreational":
        recreational_list[8]= recreational_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Recreational":
        recreational_list[9]= recreational_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Recreational":
        recreational_list[10]= recreational_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Recreational":
        recreational_list[11]= recreational_list[11] + instance.amount


      # amount for miscellaneous
      if instance.date.month == 1 and instance.category == "Miscellaneous":
        miscellaneous_list[0]= miscellaneous_list[0] + instance.amount 

      if instance.date.month == 2 and instance.category == "Miscellaneous":
        miscellaneous_list[1]= miscellaneous_list[1] + instance.amount 

      if instance.date.month == 3 and instance.category == "Miscellaneous":
        miscellaneous_list[2]= miscellaneous_list[2] + instance.amount 

      if instance.date.month == 4 and instance.category == "Miscellaneous":
        miscellaneous_list[3]= miscellaneous_list[3] + instance.amount 

      if instance.date.month == 5 and instance.category == "Miscellaneous":
        miscellaneous_list[4]= miscellaneous_list[4] + instance.amount 

      if instance.date.month == 6 and instance.category == "Miscellaneous":
        miscellaneous_list[5]= miscellaneous_list[5] + instance.amount 

      if instance.date.month == 7 and instance.category == "Miscellaneous":
        miscellaneous_list[6]= miscellaneous_list[6] + instance.amount 

      if instance.date.month == 8 and instance.category == "Miscellaneous":
        miscellaneous_list[7]= miscellaneous_list[7] + instance.amount 

      if instance.date.month == 9 and instance.category == "Miscellaneous":
        miscellaneous_list[8]= miscellaneous_list[8] + instance.amount 

      if instance.date.month == 10 and instance.category == "Miscellaneous":
        miscellaneous_list[9]= miscellaneous_list[9] + instance.amount 

      if instance.date.month == 11 and instance.category == "Miscellaneous":
        miscellaneous_list[10]= miscellaneous_list[10] + instance.amount 

      if instance.date.month == 12 and instance.category == "Miscellaneous":
        miscellaneous_list[11]= miscellaneous_list[11] + instance.amount


    for i in food_list:
      if i != 0:
        count=count+1

    for i in housing_list:
      if i != 0:
        hcount=hcount+1

    for i in transportation_list:
      if i != 0:
        tcount=tcount+1

    for i in utilities_list:
      if i != 0:
        ucount=ucount+1

    for i in insurance_list:
      if i != 0:
        icount=icount+1

    for i in medical_list:
      if i != 0:
        mcount=mcount+1

    for i in personal_list:
      if i != 0:
        pcount=pcount+1

    for i in recreational_list:
      if i != 0:
        rcount=rcount+1

    for i in miscellaneous_list:
      if i != 0:
        micount=micount+1

    sumFood=0
    sumHousing=0
    sumTransportation=0
    sumUtilities=0
    sumInsurance=0
    sumMedical=0
    sumPersonal=0
    sumRecreational=0
    sumMiscellaneous=0

    avgFood=0
    avgHousing=0
    avgTransportation=0
    avgUtilities=0
    avgInsurance=0
    avgMedical=0
    avgPersonal=0
    avgRecreational=0
    avgMiscellaneous=0

    for i in food_list:
      sumFood=sumFood+i

    for i in housing_list:
      sumHousing=sumHousing+i

    for i in transportation_list:
      sumTransportation=sumTransportation+i

    for i in utilities_list:
      sumUtilities=sumUtilities+i

    for i in insurance_list:
      sumInsurance=sumInsurance+i

    for i in medical_list:
      sumMedical=sumMedical+i

    for i in personal_list:
      sumPersonal=sumPersonal+i

    for i in recreational_list:
      sumRecreational=sumRecreational+i

    for i in miscellaneous_list:
      sumMiscellaneous=sumMiscellaneous+i

    if count ==0:
      avgFood = sumFood/1
    else:
      avgFood = sumFood/count
    if hcount ==0:
      avgHousing = sumHousing/1
    else:
      avgHousing = sumHousing/hcount
    if tcount == 0:
      avgTransportation = sumTransportation/1
    else:
      avgTransportation = sumTransportation/tcount
    if ucount == 0:
      avgUtilities = sumUtilities/1
    else:  
      avgUtilities = sumUtilities/ucount
    if icount == 0:
      avgInsurance = sumInsurance/1
    else:
      avgInsurance = sumInsurance/icount
    if mcount ==0:
      avgMedical = sumMedical/1
    else:
      avgMedical = sumMedical/mcount
    if pcount ==0:
      avgPersonal = sumPersonal/1
    else:
      avgPersonal = sumPersonal/pcount
    if rcount ==0:
      avgRecreational = sumRecreational/1
    else:
      avgRecreational = sumRecreational/rcount
    if micount == 0:
      avgMiscellaneous = sumMiscellaneous/1
    else:
      avgMiscellaneous = sumMiscellaneous/micount

    queryset = SetAside.objects.filter(username=request.user)
    queryset.delete()

    new_setAside = SetAside.objects.create(username=username, category="Food",amount=avgFood)
    
    new_setAside = SetAside.objects.create(username=username, category="Housing",amount=avgHousing)
    
    new_setAside = SetAside.objects.create(username=username, category="Transportation",amount=avgTransportation)
    
    new_setAside = SetAside.objects.create(username=username, category="Utilities",amount=avgUtilities)
    
    new_setAside = SetAside.objects.create(username=username, category="Insurance",amount=avgInsurance)
    
    new_setAside = SetAside.objects.create(username=username, category="Medical",amount=avgMedical)
   
    new_setAside = SetAside.objects.create(username=username, category="Personal",amount=avgPersonal)
    
    new_setAside = SetAside.objects.create(username=username, category="Recreational",amount=avgRecreational)
    
    new_setAside = SetAside.objects.create(username=username, category="Miscellaneous",amount=avgMiscellaneous)
    new_setAside.save()
    
    itemsWithinBudget = getDataByPrice(request)

    if request.method == "POST":
        get_user = User.objects.get(username=request.user)
        if request.POST.get("addGoals"):
            username = request.user
            priority = request.POST.get("Priority")
            if priority == "":
              messages.error(request, "Please enter your priority.")
              return redirect('budget')
            goal_Name = request.POST.get("Goal Name")
            if goal_Name == "":
              messages.error(request, "Please enter the name of your goal.")
              return redirect('budget')
            value = request.POST.get("Value")
            if value == "":
              messages.error(request, "Please enter the value of your goal.")
              return redirect('budget')
            target_Duration = request.POST.get("Target Duration")
            if target_Duration == "":
              messages.error(request, "Please enter the duration of your goal.")
              return redirect('budget')

            if target_Duration.isdigit() == False:
              messages.error(request, "Please enter in the target duration in integer only.")
              return redirect('budget')

            if not isfloat(value):
              messages.error(request, "Please fill in your goal value in decimal number only.")
              return redirect('budget')

            get_user.leftOver = float(get_user.net_worth) 
            - float(get_user.dividends) - float(get_user.interest) - float(get_user.food) 
            - float(get_user.housing) - float(get_user.transportation) - float(get_user.utilities)
            - float(get_user.insurance) - float(get_user.medical) - float(get_user.personal)
            - float(get_user.recreational) - float(get_user.miscellaneous)

            get_user.goalPrice = float(value)/float(target_Duration)


            if get_user.leftOver/30 < get_user.goalPrice:
              remarks = "It is not possible to achieve this goal, please delete this goal and choose wisely"
            else:
              remarks = "You must save up $" + str(round(get_user.goalPrice*30,2)) + " per month or $" + str(round(get_user.goalPrice,2)) + " per day."
          
        new_budget = Budget.objects.create(
            username=username, priority=priority, goal_Name=goal_Name, value=value, target_Duration=target_Duration,remarks = remarks, per_month=round(get_user.goalPrice*30,2))
        new_budget.save()


    queryset = SetAside.objects.filter(username=request.user)
    b=Budget.objects.filter(username=request.user)

    context = {
      "Oobject_list": queryset,
      "Object_list": b,
      "itemsWithinBudget" : itemsWithinBudget,
    }
    return render(request, "SetGoals.html", context)

  else:
    return redirect('Login-page')

def getDataByPrice(request):
  b = Budget.objects.filter(username=request.user)
  u = User.objects.get(username=request.user).net_worth
  maxValue = 0
  for instance in b:
    maxValue = max(u - instance.per_month/30, maxValue)
    print(instance.per_month)
  
  print(maxValue)
  imported = dataGovAPI()
  datasetid, size = imported.getDatasetID(0)
  dataset = imported.getDataset(datasetid,size)['result']['records']
  # print(dataset['result']['records'][1]['value'])
  updatedDB = []
  for data in dataset:
    if (data['value'] != 'na') and float(data['value']) <= maxValue:
      updatedDB.append(data)
  print(updatedDB)
  return updatedDB

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

# Account Verification / Creation Views


def Register(request):
  if request.method == "POST":
    Username = request.POST.get("Username")
    FirstName = request.POST.get("firstName")
    LastName = request.POST.get("lastName")
    Email = request.POST.get("email")
    Password1 = request.POST.get("password1")
    Password2 = request.POST.get("password2")

    if Username == "" or FirstName == "" or LastName == "" or Email == "" or Password1 == "" or Password2 == "":
      messages.error(request, "Please fill in all fields.")
      return redirect('Reg')

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
        if username == "":
          messages.error(request, "Please fill in all fields.")
          return redirect('Login-page')
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

    if verification == "":
      messages.error(request, "Please enter verification code.")
      return redirect('Verifying', email=email)

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
