# Manipal Airlines - Full Project Context

This document contains the complete, highly detailed context of the `airline_project` (Manipal Airlines Reservation System), specifically updated to reflect the latest interactive seat selection capabilities. You can provide this to Claude or another LLM for code analysis, architecture breakdown, or report generation.

## Project Structure Overview

- **`airline_project/`**: Main Django project configuration folder.
  - `settings.py`: Project settings, database configuration (SQLite), installed apps.
  - `urls.py`: Main URL routing.
- **`flights/`**: Primary Django app containing the core business logic.
  - `models.py`: Database schema (Airport, Flight, Booking, UserProfile) with dynamic seat tracking and JSON arrays for booked seat layouts.
  - `views.py`: Request handlers for searching, advanced booking (including checking dynamic seat overlap validation and real-time class capacity), dynamic price prediction logic, user authentication, and profile management.
  - `urls.py`: App-level routing.
  - `forms.py`: Django forms (FlightSearchForm, BookingForm with `selected_seats` field, RegistrationForm, ProfileForm).
- **`static/js/`**:
  - `main.js`: Main Javascript covering interactive UI, class selection styling, and scroll animations.
- **`templates/flights/`**: HTML templates. `book_flight.html` has interactive JS map components, an interactive seat map generation logic relying on Leaflet JS for routing maps, and Chart.js for price predictions.

---

## Source Code

### 1. `airline_project/settings.py`
```python
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-q8ny59s3_z!ee$t0!@+hujv*i7#a)(j7v#9vkzj!ws*ic569wd'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'flights',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'airline_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'airline_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### 2. `airline_project/urls.py`
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('flights.urls')),
]
```

### 3. `flights/models.py`
```python
from django.db import models
from django.contrib.auth.models import User
import json


class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True)  # IATA code
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.city} ({self.code})"

    class Meta:
        ordering = ['city']


class Flight(models.Model):
    flight_number = models.CharField(max_length=10)
    airline = models.CharField(max_length=100, default='Manipal Airlines')
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departures')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='arrivals')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    economy_price = models.DecimalField(max_digits=10, decimal_places=2)
    business_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_economy_seats = models.IntegerField(default=150)
    total_business_seats = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    stops = models.TextField(default='[]', blank=True)  # JSON list of airport codes for layovers

    def get_stops(self):
        """Return list of stop Airport objects in order."""
        try:
            codes = json.loads(self.stops)
            if codes:
                airports = Airport.objects.filter(code__in=codes)
                airport_map = {a.code: a for a in airports}
                return [airport_map[c] for c in codes if c in airport_map]
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def get_route_data(self):
        """Return full route as JSON-safe list of dicts for the map."""
        route = []
        route.append({
            'code': self.origin.code,
            'city': self.origin.city,
            'lat': self.origin.latitude,
            'lng': self.origin.longitude,
            'type': 'origin'
        })
        for stop in self.get_stops():
            route.append({
                'code': stop.code,
                'city': stop.city,
                'lat': stop.latitude,
                'lng': stop.longitude,
                'type': 'stop'
            })
        route.append({
            'code': self.destination.code,
            'city': self.destination.city,
            'lat': self.destination.latitude,
            'lng': self.destination.longitude,
            'type': 'destination'
        })
        return route

    def __str__(self):
        return f"{self.flight_number}: {self.origin.code} → {self.destination.code}"

    @property
    def duration(self):
        delta = self.arrival_time - self.departure_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return f"{hours}h {minutes}m"

    @property
    def economy_seats_available(self):
        booked = self.bookings.filter(seat_class='economy', status='confirmed').aggregate(
            total=models.Sum('num_passengers'))['total'] or 0
        return self.total_economy_seats - booked

    @property
    def business_seats_available(self):
        booked = self.bookings.filter(seat_class='business', status='confirmed').aggregate(
            total=models.Sum('num_passengers'))['total'] or 0
        return self.total_business_seats - booked

    def get_booked_seats(self, seat_class):
        bookings = self.bookings.filter(seat_class=seat_class, status='confirmed')
        booked = []
        for b in bookings:
            try:
                seats = json.loads(b.selected_seats)
                booked.extend(seats)
            except (json.JSONDecodeError, AttributeError):
                pass
        return booked

    class Meta:
        ordering = ['departure_time']


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    SEAT_CHOICES = [
        ('economy', 'Economy'),
        ('business', 'Business'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='bookings')
    seat_class = models.CharField(max_length=10, choices=SEAT_CHOICES)
    num_passengers = models.IntegerField(default=1)
    passenger_names = models.TextField(default='[]')  # JSON list of names
    selected_seats = models.TextField(default='[]')  # JSON list of seat IDs
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='confirmed')
    booking_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    booking_reference = models.CharField(max_length=8, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            import random
            import string
            self.booking_reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

    def get_passenger_names(self):
        try:
            return json.loads(self.passenger_names)
        except json.JSONDecodeError:
            return []

    def get_selected_seats(self):
        try:
            return json.loads(self.selected_seats)
        except (json.JSONDecodeError, AttributeError):
            return []
        except json.JSONDecodeError:
            return []

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.user.username}"

    class Meta:
        ordering = ['-booking_date']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Profile: {self.user.username}"
```

### 4. `flights/views.py`
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime
import json

from .models import Airport, Flight, Booking, UserProfile
from .forms import FlightSearchForm, BookingForm, RegistrationForm, ProfileForm


def home(request):
    form = FlightSearchForm()
    popular_destinations = Airport.objects.all()[:6]
    return render(request, 'flights/home.html', {
        'form': form,
        'popular_destinations': popular_destinations,
    })


def search_flights(request):
    flights = []
    passengers = 1
    origin = None
    destination = None
    date = None

    if request.GET:
        form = FlightSearchForm(request.GET)
        if form.is_valid():
            origin = form.cleaned_data['origin']
            destination = form.cleaned_data['destination']
            date = form.cleaned_data['date']
            passengers = form.cleaned_data['passengers']

            flights = Flight.objects.filter(
                origin=origin,
                destination=destination,
                departure_time__date=date,
                is_active=True
            )
    else:
        form = FlightSearchForm()

    return render(request, 'flights/search_results.html', {
        'form': form,
        'flights': flights,
        'passengers': passengers,
        'origin': origin,
        'destination': destination,
        'date': date,
    })


@login_required
def book_flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    passengers = int(request.GET.get('passengers', 1))

    if request.method == 'POST':
        form = BookingForm(request.POST, num_passengers=passengers)
        if form.is_valid():
            seat_class = form.cleaned_data['seat_class']
            selected_seats_raw = form.cleaned_data.get('selected_seats', '[]')
            try:
                selected_seats = json.loads(selected_seats_raw)
            except json.JSONDecodeError:
                selected_seats = []
                
            passenger_names = []
            for i in range(passengers):
                name = form.cleaned_data.get(f'passenger_{i+1}', '')
                if name:
                    passenger_names.append(name)

            # Check availability
            if seat_class == 'economy':
                if flight.economy_seats_available < passengers:
                    messages.error(request, 'Not enough economy seats available!')
                    return redirect('book_flight', flight_id=flight.id)
                price_per_seat = flight.economy_price
            else:
                if flight.business_seats_available < passengers:
                    messages.error(request, 'Not enough business seats available!')
                    return redirect('book_flight', flight_id=flight.id)
                price_per_seat = flight.business_price
                
            if len(selected_seats) != passengers:
                messages.error(request, f'Please select exactly {passengers} seat(s).')
                return redirect('book_flight', flight_id=flight.id)
                
            booked_so_far = flight.get_booked_seats(seat_class)
            overlap = set(selected_seats).intersection(set(booked_so_far))
            if overlap:
                messages.error(request, f'One or more selected seats ({", ".join(overlap)}) are already booked.')
                return redirect('book_flight', flight_id=flight.id)

            total_price = price_per_seat * passengers

            booking = Booking.objects.create(
                user=request.user,
                flight=flight,
                seat_class=seat_class,
                num_passengers=passengers,
                passenger_names=json.dumps(passenger_names),
                selected_seats=json.dumps(selected_seats),
                total_price=total_price,
            )

            messages.success(request, f'Booking confirmed! Reference: {booking.booking_reference}')
            return redirect('booking_confirmation', booking_id=booking.id)
    else:
        form = BookingForm(num_passengers=passengers)

    route_data = json.dumps(flight.get_route_data())

    # --- Price Predictor ---
    import hashlib
    import random as rng
    from datetime import timedelta
    from django.utils import timezone

    # Generate deterministic simulated price history (7 days)
    seed = int(hashlib.md5(str(flight.id).encode()).hexdigest()[:8], 16)
    rng_gen = rng.Random(seed)

    base_price = float(flight.economy_price)
    today = timezone.now().date()
    price_history = []
    prices = []

    for i in range(7):
        day = today - timedelta(days=6 - i)
        # Simulate price fluctuation: -8% to +10% from base with a slight upward trend
        variation = rng_gen.uniform(-0.08, 0.10) + (i * 0.005)
        day_price = round(base_price * (1 + variation) / 100) * 100
        price_history.append({
            'date': day.strftime('%d %b'),
            'price': day_price
        })
        prices.append(day_price)

    # Compute trend: compare average of last 3 days vs first 3 days
    avg_recent = sum(prices[-3:]) / 3
    avg_earlier = sum(prices[:3]) / 3
    current_price = prices[-1]
    price_change_pct = ((avg_recent - avg_earlier) / avg_earlier) * 100

    if price_change_pct > 3:
        prediction = 'rising'
        recommendation = 'Book Now'
        rec_detail = 'Prices are trending upward. Lock in today\'s rate before it increases further.'
        rec_color = '#c45c5c'
    elif price_change_pct < -3:
        prediction = 'falling'
        recommendation = 'Wait'
        rec_detail = 'Prices have been dropping. You might get a better deal in the next few days.'
        rec_color = '#c9952c'
    else:
        prediction = 'stable'
        recommendation = 'Good Time to Book'
        rec_detail = 'Prices are stable right now. This is a fair price for this route.'
        rec_color = '#6b9e6e'

    price_prediction = json.dumps({
        'history': price_history,
        'prediction': prediction,
        'recommendation': recommendation,
        'detail': rec_detail,
        'color': rec_color,
        'current_price': current_price,
        'change_pct': round(price_change_pct, 1),
    })

    booked_economy_seats = json.dumps(flight.get_booked_seats('economy'))
    booked_business_seats = json.dumps(flight.get_booked_seats('business'))

    return render(request, 'flights/book_flight.html', {
        'flight': flight,
        'form': form,
        'passengers': passengers,
        'route_data': route_data,
        'price_prediction': price_prediction,
        'booked_economy_seats': booked_economy_seats,
        'booked_business_seats': booked_business_seats,
    })


@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    route_data = json.dumps(booking.flight.get_route_data())
    return render(request, 'flights/booking_confirmation.html', {
        'booking': booking,
        'route_data': route_data,
    })


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)

    # Build travel map data from confirmed bookings
    visited_airports = {}
    routes = []
    for booking in bookings.filter(status='confirmed'):
        origin = booking.flight.origin
        dest = booking.flight.destination
        # Track unique airports
        if origin.code not in visited_airports:
            visited_airports[origin.code] = {
                'code': origin.code, 'city': origin.city,
                'lat': origin.latitude, 'lng': origin.longitude
            }
        if dest.code not in visited_airports:
            visited_airports[dest.code] = {
                'code': dest.code, 'city': dest.city,
                'lat': dest.latitude, 'lng': dest.longitude
            }
        # Track routes
        routes.append({
            'from': {'lat': origin.latitude, 'lng': origin.longitude, 'code': origin.code},
            'to': {'lat': dest.latitude, 'lng': dest.longitude, 'code': dest.code},
            'flight': booking.flight.flight_number
        })

    travel_map_data = json.dumps({
        'airports': list(visited_airports.values()),
        'routes': routes
    })

    return render(request, 'flights/my_bookings.html', {
        'bookings': bookings,
        'travel_map_data': travel_map_data,
        'total_cities': len(visited_airports),
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status == 'confirmed':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, f'Booking {booking.booking_reference} has been cancelled.')
    else:
        messages.warning(request, 'This booking is already cancelled.')
    return redirect('my_bookings')


@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()

            user_profile.phone = form.cleaned_data['phone']
            user_profile.address = form.cleaned_data['address']
            user_profile.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': user_profile.phone,
            'address': user_profile.address,
        })

    return render(request, 'flights/profile.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Welcome aboard! Your account has been created.')
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'flights/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'flights/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')
```

### 5. `flights/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_flights, name='search_flights'),
    path('book/<int:flight_id>/', views.book_flight, name='book_flight'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
```

### 6. `flights/forms.py`
```python
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
    selected_seats = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'selected_seats'}),
        required=True,
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
```

### 7. `flights/templates/flights/book_flight.html`
*(Truncated for brevity but representing the core logic)*
Contains comprehensive interactive systems:
- Visual interactive Leaflet-based map integration.
- Dynamic responsive seat map generation using custom Javascript `generateSeatMap()` interacting with Django arrays tracking `booked_business_seats` & `booked_economy_seats`. 
- Price Prediction chart.js initialization with trend suggestions.

### 8. `static/js/main.js`
```javascript
// Mobile nav toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });

        // Close nav when clicking a link on mobile
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
            });
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Fade-in animation on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card, .dest-card').forEach(el => {
        observer.observe(el);
    });

    // Seat class selection - update price display
    const seatRadios = document.querySelectorAll('input[name="seat_class"]');
    seatRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            document.querySelectorAll('.seat-option-label').forEach(label => {
                label.style.borderColor = '';
                label.style.background = '';
                label.style.boxShadow = '';
            });
            if (this.checked) {
                const label = this.nextElementSibling || this.closest('.seat-option').querySelector('.seat-option-label');
                if (label) {
                    label.style.borderColor = 'var(--accent)';
                    label.style.background = 'var(--accent-dim)';
                    label.style.boxShadow = '0 0 12px var(--accent-glow)';
                }
            }
        });
    });
});
```
