from django.contrib import admin
from listings.models import Listing


#List of listings
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'is_approved') 
    #The list of listings will display the title, description, and is_approved value of the listing
    #click on the listing title to view all of that specific title's information (photos, price, etc)

#UnapprovedListing is a proxy of Listing, i.e. it inherits the values of Listing
class UnapprovedListing(Listing):
	class Meta:
		proxy = True

#List of all unapproved listings (all listings with is_approved == False)
class UnapprovedListingAdmin(ListingAdmin):
	list_display = ('title', 'description')
	#Display the title and description of each listing in the list
	#Clicking on the title of the listing takes you to a separate page to view all of its infor 

	#This returns all listings in Listing that are unapproved
	def get_queryset(self, request):
		return self.model.objects.filter(is_approved = False)



admin.site.register(Listing, ListingAdmin)
admin.site.register(UnapprovedListing, UnapprovedListingAdmin)

'''
if Listing.objects.filter(is_approved = False).count() > 0: 
	admin.site.register(UnapprovedListing, UnapprovedListingAdmin)

Only displays the list if there is at least one unapproved listing, but the server must be restarted for it to take effect 
Will look into this later
'''