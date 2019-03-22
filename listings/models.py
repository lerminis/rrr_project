from django.db import models
from abc import ABCMeta, abstractmethod
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django_postgres_extensions.models.functions import ArrayRemove, ArrayAppend
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail


# FACTORY PATTERN
class Creator:
    """
    Declares the factory method, and returns an object of type Message.
    The object will either be a success, error, or warning message
    Success is chosen when a successful operation has been performed (eg. successful account creation)
    Error is chosen when an operation has failed (eg. the user entered an incorrect while trying to update their account info)
    Warning is chosen when a user marks any of their listings as unavailable
    The appropriate message will then be displayed to the user
    """
    __metaclass__ = ABCMeta

    def __init__(self, request, context, message):
        """Initialize object state"""
        self.request = request
        self.context = context
        self.message = message

    @abstractmethod
    def create(self):
        """Creates a message object based on the type of message to display to the user"""
        pass


class ConcreteCreator(Creator):

    def create(self):
        """Creates an object based on the context of what just happened"""
        if (self.context == "success"):  # Success
            return ConcreteSuccessMessage(self.request, self.context, self.message)
        elif (self.context == "error"):  # Error
            return ConcreteErrorMessage(self.request, self.context, self.message)
        else:  # Warning
            return ConcreteWarningMessage(self.request, self.context, self.message)


class Message:
    """Abstract class for all three message classes"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def display(self):
        pass


class ConcreteSuccessMessage(Creator, Message):
    """Success message"""

    def display(self):
        messages.success(self.request, self.message)


class ConcreteErrorMessage(Creator, Message):
    """Error message"""

    def display(self):
        messages.error(self.request, self.message)


class ConcreteWarningMessage(Creator, Message):
    """Warning message"""

    def display(self):
        messages.warning(self.request, self.message)


# OBSERVER PATTERN
class Subject:
    """Provides an 'interface' for attaching and detaching Observer objects."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def register(self, observer):
        """Registers an observer to Subject."""
        pass

    @abstractmethod
    def remove(self, observer):
        """Removes an observer from Subject."""
        pass

    @abstractmethod
    def notify(self):
        """Notifies observers that Subject data has changed."""
        pass


class Observer:
    """Defines an updating 'interface' for objects that should be notified of changes in a subject."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        """Observer notifies subject that it has become aware of the changes."""
        pass


class ConcreteObserver(User, Observer):
    """
    The default User model acts as the concrete observer, implements the Observer 'interface'. 
    Creates a proxy to Django's default User model so it can access the same table in the database
    """
    class Meta:
        proxy = True

    def update(self, subject):
        # print('Subscriber {0} was successfully notified about the availability of {1}'.format(
        #     self.username, subject))
        esubject = '[RRR] Subscriber Notification'
        message = 'Hey {0}! We wanted to let you know that user "{1}" was successfully notified about the recent availability of your listing "{2}"'.format(subject.user.first_name, self.username, subject.title)
        message = message + '\n\nThanks!\n\nRRR Notifications Team \n\nThis is an automated email. Do not respond to this email!'
        from_email = settings.EMAIL_HOST_USER
        to_email = [subject.user.email]
        send_mail(esubject, message, from_email, to_email, fail_silently=True)


class Listing(models.Model, Subject):
    """The custom Listing model acts as the concrete subject, implements the Subject 'interface'."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    location = models.IntegerField()
    description = models.TextField()
    daily_price = models.IntegerField()
    photo_1 = models.ImageField(upload_to='photos/%Y/%m/%d/')
    photo_2 = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True)
    photo_3 = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True)
    photo_4 = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True)
    photo_5 = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True)
    is_available = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    subscribers = ArrayField(
        models.EmailField(blank=True),
        default=list,
        blank=True,
    )

    class Meta:
        db_table = 'listings_listing'  # table name

    def __str__(self):
        return self.title

    def register(self, observer):
        if observer not in self.subscribers:
            self.subscribers = ArrayAppend('subscribers', observer)
            super(Listing, self).save()
        else:
            print('Already subscribed!')

    def remove(self, observer):
        try:
            self.subscribers = ArrayRemove('subscribers', observer)
            super(Listing, self).save()
        except ValueError:
            print('Failed to remove!')

    def notify(self):
        subject = '[RRR] {} is now available!'.format(self.title)
        message = 'Hey! You were subscribed to {0} and we just wanted to let you know it is now available to be rented!'.format(self.title)
        message = message + '\n\nThanks!\n\nRRR Notifications Team \n\nThis is an automated email. Do not respond to this email!'
        from_email = settings.EMAIL_HOST_USER
        to_email = []
        for sub in self.subscribers:
            ConcreteObserver.objects.get(email=sub).update(self)
            to_email.append(sub)  # adds all subscribers to the emailing list

        # send the email to all subscribers
        send_mail(subject, message, from_email, to_email, fail_silently=True)
