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

            total_price = price_per_seat * passengers

            booking = Booking.objects.create(
                user=request.user,
                flight=flight,
                seat_class=seat_class,
                num_passengers=passengers,
                passenger_names=json.dumps(passenger_names),
                total_price=total_price,
            )

            messages.success(request, f'Booking confirmed! Reference: {booking.booking_reference}')
            return redirect('booking_confirmation', booking_id=booking.id)
    else:
        form = BookingForm(num_passengers=passengers)

    return render(request, 'flights/book_flight.html', {
        'flight': flight,
        'form': form,
        'passengers': passengers,
    })


@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'flights/booking_confirmation.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'flights/my_bookings.html', {'bookings': bookings})


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
