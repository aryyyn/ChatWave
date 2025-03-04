from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import login,authenticate,logout
from .models import CustomUser
from django.core.exceptions import ValidationError
from Profile.models import Playlists
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import random
from django.contrib.auth.hashers import make_password
import re
load_dotenv()



def RegisterLogic(request):

    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('homeChatViewLogic')

           
    if request.method == "POST":
        # Extracting form data
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmpassword = request.POST.get("confirmpassword")
        profilePicture = "https://i.pinimg.com/736x/4c/d2/a6/4cd2a6615820a4a15f4d85de7762251d.jpg"

        
        if not all([username, email, password, confirmpassword]):
            messages.error(request, "All fields are required.")
        

        elif password != confirmpassword:
            messages.error(request, "Passwords do not match.")


        elif not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter.")

        elif not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter.")

        elif not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one digit.")

        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must contain at least one special character.")
        

        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
       

        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            try:
               
                user = CustomUser.objects.create_user(username=username, email=email, password=password, profilePicture=profilePicture)
                Playlists.objects.create(playlist_name="indie", user=user)
                Playlists.objects.create(playlist_name="pop", user=user)
                Playlists.objects.create(playlist_name="rap", user=user)
                Playlists.objects.create(playlist_name="hiphop", user=user)
                Playlists.objects.create(playlist_name="lofi", user=user)
                Playlists.objects.create(playlist_name="edm", user=user)
                messages.success(request, "Successfully registered! You can now log in.")
                email_logic(user, email)
                return render(request, "login/loginbase.html")
            except ValidationError as v:
                messages.error(request, f"{v}")
            except Exception as e:
                messages.error(request, f"{e}")

        # If there's an error, return to the registration page
        return render(request, "register/registerbase.html", {"username": username, "email": email})

   
    return render(request, "register/registerbase.html")


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = CustomUser.objects.filter(email=email).first()

        if user:
            user.verification_code = random.randint(100000, 999999)
            user.save()
            email_logic(user, email)
            return redirect("new_password")
        else:
            messages.error(request, "Email Does Not Exist.")
            return render(request, "forgot_password/forgot_password.html")

    return render(request, "forgot_password/forgot_password.html")


import re
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login


def newPassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = CustomUser.objects.filter(email=email).first()

        if not user:
            messages.error(request, "Incorrect Email!")
            return render(request, "forgot_password/new_password.html")

        user_code = "".join([request.POST.get(f"code-{i}", "") for i in range(1, 7)])
        newPassword = request.POST.get("new-password")
        confirmPassword = request.POST.get("confirm-password")

        code_in_db = str(user.verification_code) if user.verification_code else ""

        if user_code == code_in_db:
            if newPassword != confirmPassword:
                messages.error(request, "Passwords do not match!")
                return render(request, "forgot_password/new_password.html")

            elif len(newPassword) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, "forgot_password/new_password.html")

            elif not re.search(r'[A-Z]', newPassword):
                messages.error(request, "Password must contain at least one uppercase letter.")
                return render(request, "forgot_password/new_password.html")

            elif not re.search(r'[a-z]', newPassword):
                messages.error(request, "Password must contain at least one lowercase letter.")
                return render(request, "forgot_password/new_password.html")

            elif not re.search(r'\d', newPassword):
                messages.error(request, "Password must contain at least one digit.")
                return render(request, "forgot_password/new_password.html")

            elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', newPassword):
                messages.error(request, "Password must contain at least one special character.")
                return render(request, "forgot_password/new_password.html")
            
            user.set_password(newPassword) 
            user.save()

            login(request, user) 
            return redirect("homeChatViewLogic") 

        else:
            messages.error(request, "Invalid Verification Code!")
            return render(request, "forgot_password/new_password.html")

    return render(request, "forgot_password/new_password.html")


def email_logic(user, email):
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')

    try:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = email
        message['Subject'] = "Verification Code for ChatWave"
        message.attach(MIMEText(f"Your verification code for ChatWave is {user.verification_code}", 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()

        print("Email sent successfully!")
        return "Success"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return "Failure"



def loginLogic(request):

    if request.method == "GET":  
        if request.user.is_authenticated: #check if the user is already logged in, if yes, then redirect them to the dashboard instead of the login page
            return redirect('homeChatViewLogic')
            #return redirect("homepage")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)  #check if the info is correct, and if it returns any user
        
        if user is not None:
            if user.is_verified == False:
                login(request, user)
                return redirect("verification_logic")
            else:
                login(request, user) #login the user if the info is correct
                return redirect('homeChatViewLogic')
        else:
            messages.error(request, "Invalid Login Info")

    return render(request, "login/loginbase.html")


def logoutLogic(request):
    logout(request) #simple logic to logout the user
    return redirect("login_logic")


def verificationLogic(request):

    if request.user.is_authenticated and not request.user.is_verified:
        if request.method == "GET":
            return render(request, "verification/verification.html")
        if request.method == "POST":
            user_code = "".join([request.POST.get(f"code-input-{i}") for i in range(1, 7)])

            code_in_db = str(request.user.verification_code)
            
            if (user_code == code_in_db):
                request.user.is_verified = True
                request.user.save()
                return redirect('homeChatViewLogic')
            
            else:
                messages.error(request, "Invalid Verification Code")
                return render(request, "verification/verification.html")
                # return redirect('verification_logic')
        #compare this code with the code that was sent to the email, and if the code is correct, then change the verification status and redirect them to the homepage
        
        