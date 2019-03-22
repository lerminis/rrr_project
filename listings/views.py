from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ListingForm
from .models import Listing,  ConcreteCreator
from django.core.paginator import Paginator
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django_postgres_extensions.models.functions import ArrayRemove, ArrayAppend
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Allows for filtering in listings
def listings(request):
    # search query (= None if q POST var isnt set)
    query = request.GET.get('q')
    if query is not None:
        approved_listings_query = Listing.objects.filter(is_approved=True, title__icontains=query).order_by('-id')  # gets all approved listings, and sorts by id in ascending order
    else:
        approved_listings_query = Listing.objects.filter(is_approved=True).order_by('-id')  # query wasn't entered - display ALL approved listings

    available = request.GET.get('available')
    if available is not None:
        approved_listings_query = approved_listings_query.filter(is_available=True)

    daily_price = request.GET.get('daily_price')
    if daily_price is not None:
        daily_price = int(daily_price)
        if daily_price == 0:
            approved_listings_query = approved_listings_query.filter(daily_price__range=(0, 14))
        elif daily_price == 1:
            approved_listings_query = approved_listings_query.filter(daily_price__range=(15, 30))
        elif daily_price == 2:
            approved_listings_query = approved_listings_query.filter(daily_price__range=(31, 50))
        elif daily_price == 3:
            approved_listings_query = approved_listings_query.filter(daily_price__range=(51, 75))
        else:
            approved_listings_query = approved_listings_query.filter(daily_price__range=(76, 1000))

    location = request.GET.get('location')
    if location is not None:
        location = int(location)
        if location == 0:
            approved_listings_query = approved_listings_query.filter(location=0)
        elif location == 1:
            approved_listings_query = approved_listings_query.filter(location=1)
        elif location == 2:
            approved_listings_query = approved_listings_query.filter(location=2)
        else:
            approved_listings_query = approved_listings_query.filter(location=3)

    paginator = Paginator(approved_listings_query, 3)  # 3 listings per page
    page = request.GET.get('page')  # gets page number from url
    # gets the approved listings from some page number
    approved_listings = paginator.get_page(page)
    return render(request, 'listings/viewlistings.html', {'approved_listings': approved_listings, 'count': approved_listings_query.count, 'query': query})

#Specific listing, allows for subscription
def listing(request, listing_id):
    specific_listing = Listing.objects.get(id=listing_id)
    context = {
        'title': specific_listing.title,
        'location': specific_listing.location,
        'description': specific_listing.description,
        'daily_price': specific_listing.daily_price,
        'photo_1': specific_listing.photo_1,
        'photo_2': specific_listing.photo_2,
        'photo_3': specific_listing.photo_3,
        'photo_4': specific_listing.photo_4,
        'photo_5': specific_listing.photo_5,
        'is_available': specific_listing.is_available,
        'user': specific_listing.user,
        'id': listing_id,
        'is_approved': specific_listing.is_approved,
    }

    
    #Users can't view other user's non-approved listings (However they can view their own non-approved listings)
    if specific_listing.is_approved is False and (str(request.user.username) != str(context['user'])): 
        message = ConcreteCreator(request, "error", "You can't view other users listings which have not yet been approved by the admin!").create()
        message.display()
        return redirect('listings')


    # the message entered by the user to send to the listing owner
    email_msg = request.POST.get('email_msg', 0)
    if email_msg is not 0:  # if the user clicked on the submit message button
        #Email sent using GMAIL
        subject = '[RRR] New inquiry from user "{0}" regarding your listing "{1}"'.format(request.user.username, context['title'])
        email_msg = email_msg + '\n\nRespond to {0} with the following email: {1}\n\nThanks!\n\nRRR Notifications Team \n\nThis is an automated email. Do not respond to this email!'.format(request.user.first_name, request.user.email)
        from_email = settings.EMAIL_HOST_USER
        to_email = [User.objects.get(username=context['user']).email] #owner of the listing

        send_mail(subject, email_msg, from_email, to_email, fail_silently=True)
        message = ConcreteCreator(request, "success", 'Email sent!').create()
        message.display()


    # OBSERVER PATTERN Subscribe
    # Set when the user clicks the subscribe button
    subscribe = request.POST.get('subscribe', 0)
    if subscribe is not 0:  # User wants to subscribe to the list

        # CALL SUBSCRIBE IN CONCRETE SUBJECT
        specific_listing.register(request.user.email)

        # add to context to determine what to display to the user
        context['subscriber'] = True
        message = ConcreteCreator(request, "success", 'Successfully subscribed!').create()
        message.display()


    # set when user clicks unsubscribe
    unsubscribe = request.POST.get('unsubscribe', 0)
    if unsubscribe is not 0:  # user wants to unsubscribe

        # CALL REMOVE IN CONCRETE SUBJECT
        specific_listing.remove(request.user.email)

        # add to context to determine what to display to the user
        context['subscriber'] = False
        message = ConcreteCreator(request, "success", 'Successfully unsubscribed!').create()
        message.display()

    return render(request, 'listings/listing.html', context)

# Create a listing
def create(request):
    if request.method == 'POST':

        context = {
            'title': request.POST['title'],
            'description': request.POST['description'],
            'daily_price': request.POST['daily_price'],
            'location': int(request.POST['location']),
        }

        # description is too short
        if (len(request.POST['description']) < 15):
            message = ConcreteCreator(request, "error", 'Description must be at least 15 characters long!').create()
            message.display()
            return render(request, 'listings/create.html', context)

        # uploaded file must be a jpg
        # goes through all the photos (photo_1 to photo_5) and checks if they exist
        # if the photo exists (ie a user uploaded that image), it must end with .jpg, .JPG, .png, .PNG
        for i in range(1, 6):
            # booleanFalse if the photo doesnt exist. If the file exists, it is equal to the name of the file (eg pairofskates.png)
            filepath = request.FILES.get('photo_' + str(i), False)
            if (filepath is not ('' or False) and not (str(filepath).endswith('.jpg') or str(filepath).endswith('.JPG') or str(filepath).endswith('.JPEG') or str(filepath).endswith('.jpeg') or str(filepath).endswith('.png') or str(filepath).endswith('.PNG'))):
                message = ConcreteCreator(request, "error", 'Uploaded files must be jpgs or pngs!').create()
                message.display()
                return render(request, 'listings/create.html', context)

        # Stores user entered information in a form automatically
        form = ListingForm(request.POST, request.FILES)

        if form.is_valid():

            newListing = form.save(commit=False)
            # foreign key - logged in user's ID (int)
            newListing.user_id = request.user.id
            newListing.save()

            message = ConcreteCreator(request, "success", 'Listing successfully created! It now awaits admin approval').create()
            message.display()
            return redirect('dashboard')

        else:  # error while trying to create a post - this should never happen
            message = ConcreteCreator(request, "error", 'Please try again').create()
            message.display()
            return render(request, 'listings/create.html', context)

    else:
        # can only view the create a listing page if they are logged in
        if not request.user.is_authenticated:
            # create a listing redirects to login when not logged in, so this redirect will happen when users type in the url for the create page instead of clicking on the button
            message = ConcreteCreator(request, "error", 'Must be logged in to create a listing!').create()
            message.display()
            return redirect('login')
        else:
            # logged in user clicked on the Create a Listing button
            return render(request, 'listings/create.html')

# Edit a listing 
def edit(request, listing_id):
    specific_listing = Listing.objects.get(id=listing_id)
        
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=specific_listing)
    
        try:
            if form.is_valid():
                form.save()
                message = ConcreteCreator(request, 0, 'Your post has been updated!').create()
                message.display()
                return redirect('dashboard')
        except Exception as e:
            message = ConcreteCreator(request, 1, 'Your post was not saved due to an error. Please try again!').create()
            message.display()

        return redirect('dashboard')

    form = ListingForm() # Make photo upload optional
    context = {
        'form' : form,
        'title': specific_listing.title,
        'location': specific_listing.location,
        'description': specific_listing.description,
        'daily_price': specific_listing.daily_price,
        'photo_1': specific_listing.photo_1,
        'photo_2': specific_listing.photo_2,
        'photo_3': specific_listing.photo_3,
        'photo_4': specific_listing.photo_4,
        'photo_5': specific_listing.photo_5
    } 

    return render(request, 'listings/edit.html', context)

# Delete a listing
def delete(request, listing_id):
    specific_listing = Listing.objects.get(id=listing_id)
    
    form = ListingForm(request.POST, instance=specific_listing)
    specific_listing.delete()
    message = ConcreteCreator(request, "success", 'Your post was successfully deleted, friend!').create()
    message.display()

    return redirect('dashboard')
