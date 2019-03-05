from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.models import User
from listings.models import Listing, ConcreteCreator
from django.core.paginator import Paginator
from .forms import RegisterForm

#Register account
def register(request): 
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            message = ConcreteCreator(request, "success", 'Your account has been created!').create()
            message.display()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'register_form': form})

#Displays user listings, allows user to mark listing as unavailable and available
def dashboard(request):
    user_listings_query = Listing.objects.filter(user_id=request.user).order_by('id')
    paginator = Paginator(user_listings_query, 10)
    page = request.GET.get('page')
    user_listings = paginator.get_page(page)

    if request.method == 'POST':
        specific_listing = Listing.objects.get(id=request.POST['set_rented'])
        if specific_listing.is_available is True:
            specific_listing.is_available = False
            specific_listing.save()
            message = ConcreteCreator(request, "warning", str(specific_listing) + ' will no longer be shown as available!').create()
            message.display()
        else:
            specific_listing.is_available = True
            specific_listing.save()
            specific_listing.notify()
            message = ConcreteCreator(request, "success", str(specific_listing) + ' will now be available for others to rent! Subscribers will also be notified').create()
            message.display()

    return render(request, 'accounts/dashboard.html', {'user_listings_query': user_listings_query, 'user_listings': user_listings})

#Edit profile, allows user to edit fields on profile page
def profile(request):
    if request.user.is_authenticated is False:  # User must be logged in to view their Edit Profile page
        message = ConcreteCreator(request, "error", 'You must be logged in to view this page!').create()
        message.display()
        return redirect('login')

    user_account = User.objects.get(id=request.user.id)
    context = {
        'first_name': user_account.first_name,
        'last_name': user_account.last_name,
        'username': user_account.username,
        'email': user_account.email,
    }

    if request.method == 'POST':  # User changed their info
        first_name = request.POST.get('first_name', 0)
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password', 0)
        confirm_new_password = request.POST.get('confirm_new_password', 0)
        old_password = request.POST.get('old_password', "blank")

        # one or more required fields left blank
        if not (first_name and last_name and username and email and old_password):
            message = ConcreteCreator(request, "error", 'Only the new password fields can be left blank! Please try again').create()
            message.display()
            return render(request, 'accounts/profile.html', context)

        if confirm_new_password != new_password:  # new password and confirm new password didnt match
            message = ConcreteCreator(request, "error", 'New password fields did not match! Please try again').create()
            message.display()
            return render(request, 'accounts/profile.html', context)

        # true when old_password matches the users actual password
        check_password = auth.authenticate(username=request.user.username, password=old_password)

        if check_password is None:  # User entered an incorrect password
            message = ConcreteCreator(request, "error", 'Invalid old password! Please try again').create()
            message.display()
            return render(request, 'accounts/profile.html', context)

        # username already exists
        if User.objects.filter(username=username).exists() and (username != context['username']):
            message = ConcreteCreator(request, "error", 'Username already taken!').create()
            message.display()
            return render(request, 'accounts/profile.html', context)

        # email already exists
        if User.objects.filter(email=email).exists() and (email != context['email']):
            message = ConcreteCreator(request, "error", 'Email already taken!').create()
            message.display()
            return render(request, 'accounts/profile.html', context)

        # Update account information
        user_account.first_name = first_name
        user_account.last_name = last_name
        user_account.username = username
        user_account.email = email

        # update the context to display the updated details when the profile page reloads
        context['first_name'] = first_name
        context['last_name'] = last_name
        context['username'] = username
        context['email'] = email

        if new_password:  # Update password only if a new one was entered
            user_account.set_password(new_password)

        user_account.save()
        message = ConcreteCreator(request, "success", 'Info successfully updated!').create()
        message.display()

        if new_password:  # Must re-login if a new password has been set, or you will be logged out when updating your password
            auth.login(request, auth.authenticate(
                username=username, password=new_password))

    return render(request, 'accounts/profile.html', context)
