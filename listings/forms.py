from django import forms
from .models import Listing

class ListingForm(forms.ModelForm):
	photo_1 = forms.FileField(required=False)
	photo_2 = forms.FileField(required=False)
	photo_3 = forms.FileField(required=False)
	photo_4 = forms.FileField(required=False)
	photo_5 = forms.FileField(required=False)

	class Meta:
		model = Listing
		fields = [
			'title',
			'location',
			'description',
			'daily_price',
			'photo_1',
			'photo_2',
			'photo_3',
			'photo_4',
			'photo_5',
		]