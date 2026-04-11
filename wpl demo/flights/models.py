from django.db import models
from django.contrib.auth.models import User
import json


class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True)  # IATA code
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')

    def __str__(self):
        return f"{self.city} ({self.code})"

    class Meta:
        ordering = ['city']


class Flight(models.Model):
    flight_number = models.CharField(max_length=10)
    airline = models.CharField(max_length=100, default='SkyWay Airlines')
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departures')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='arrivals')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    economy_price = models.DecimalField(max_digits=10, decimal_places=2)
    business_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_economy_seats = models.IntegerField(default=150)
    total_business_seats = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

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
