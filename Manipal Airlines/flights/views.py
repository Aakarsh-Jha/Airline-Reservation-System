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
