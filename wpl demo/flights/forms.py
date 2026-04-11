from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Airport


class FlightSearchForm(forms.Form):
    origin = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        empty_label="Select Origin City",
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'search-origin'})
    )
    destination = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        empty_label="Select Destination City",
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'search-destination'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'id': 'search-date'})
    )
    passengers = forms.IntegerField(
        min_value=1, max_value=9, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'id': 'search-passengers'})
    )


class BookingForm(forms.Form):
    seat_class = forms.ChoiceField(
        choices=[('economy', 'Economy'), ('business', 'Business')],
        widget=forms.RadioSelect(attrs={'class': 'seat-radio'})
    )

    def __init__(self, *args, num_passengers=1, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(num_passengers):
            self.fields[f'passenger_{i+1}'] = forms.CharField(
                max_length=100,
                label=f'Passenger {i+1} Full Name',
                widget=forms.TextInput(attrs={
                    'class': 'form-input',
                    'placeholder': f'Enter passenger {i+1} name',
                    'id': f'passenger-name-{i+1}'
                })
            )


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email address', 'id': 'reg-email'})
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name', 'id': 'reg-first-name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name', 'id': 'reg-last-name'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Username', 'id': 'reg-username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Password', 'id': 'reg-password1'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirm password', 'id': 'reg-password2'})


class ProfileForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'id': 'profile-first-name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'id': 'profile-last-name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'id': 'profile-email'})
    )
    phone = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone number', 'id': 'profile-phone'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Address', 'id': 'profile-address'})
    )
