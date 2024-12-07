from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import login,authenticate,logout
from .models import CustomUser
from django.core.exceptions import ValidationError
from Profile.models import Playlists

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

        
        if not all([username, email, password, confirmpassword]):
            messages.error(request, "All fields are required.")
        

        elif password != confirmpassword:
            messages.error(request, "Passwords do not match.")
        

        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
       

        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            try:
               
                user = CustomUser.objects.create_user(username=username, email=email, password=password)
                Playlists.objects.create(playlist_name="indie", user=user)
                Playlists.objects.create(playlist_name="pop", user=user)
                Playlists.objects.create(playlist_name="rap", user=user)
                Playlists.objects.create(playlist_name="hiphop", user=user)
                Playlists.objects.create(playlist_name="lofi", user=user)
                Playlists.objects.create(playlist_name="edm", user=user)
                messages.success(request, "Successfully registered! You can now log in.")
                return redirect("login_logic")
            except ValidationError as v:
                messages.error(request, f"{v}")
            except Exception as e:
                messages.error(request, f"{e}")

        # If there's an error, return to the registration page
        return render(request, "register/registerbase.html", {"username": username, "email": email})

   
    return render(request, "register/registerbase.html")


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
            login(request, user) #login the user if the info is correct
            return redirect('homeChatViewLogic')
        else:
            messages.error(request, "Invalid Login Info")

    return render(request, "login/loginbase.html")


def logoutLogic(request):
    logout(request) #simple logic to logout the user
    return redirect("login_logic")