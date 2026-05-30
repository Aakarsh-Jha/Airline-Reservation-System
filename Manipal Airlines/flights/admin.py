from django.contrib import admin
from .models import Airport, Flight, Booking, UserProfile


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'city', 'country')
    search_fields = ('code', 'name', 'city')


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'airline', 'origin', 'destination', 'departure_time', 'arrival_time', 'economy_price', 'business_price', 'is_active')
    list_filter = ('airline', 'is_active', 'origin', 'destination')
    search_fields = ('flight_number',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'flight', 'seat_class', 'num_passengers', 'total_price', 'status', 'booking_date')
    list_filter = ('status', 'seat_class')
    search_fields = ('booking_reference', 'user__username')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username',)
