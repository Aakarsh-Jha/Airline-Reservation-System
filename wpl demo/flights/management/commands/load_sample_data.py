from django.core.management.base import BaseCommand
from django.utils import timezone
from flights.models import Airport, Flight
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Load sample airports and flights data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating airports...')

        airports_data = [
            ('DEL', 'Indira Gandhi International Airport', 'Delhi'),
            ('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai'),
            ('BLR', 'Kempegowda International Airport', 'Bengaluru'),
            ('MAA', 'Chennai International Airport', 'Chennai'),
            ('CCU', 'Netaji Subhas Chandra Bose International Airport', 'Kolkata'),
            ('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad'),
            ('COK', 'Cochin International Airport', 'Kochi'),
            ('GOI', 'Goa International Airport', 'Goa'),
            ('JAI', 'Jaipur International Airport', 'Jaipur'),
            ('AMD', 'Sardar Vallabhbhai Patel International Airport', 'Ahmedabad'),
        ]

        airports = {}
        for code, name, city in airports_data:
            airport, created = Airport.objects.get_or_create(
                code=code,
                defaults={'name': name, 'city': city, 'country': 'India'}
            )
            airports[code] = airport
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {airport}')

        self.stdout.write('\nCreating flights...')

        airlines = ['SkyWay Airlines', 'IndiGo', 'Air India', 'SpiceJet', 'Vistara']

        routes = [
            ('DEL', 'BOM', 2.0), ('BOM', 'DEL', 2.0),
            ('DEL', 'BLR', 2.5), ('BLR', 'DEL', 2.5),
            ('BOM', 'BLR', 1.5), ('BLR', 'BOM', 1.5),
            ('DEL', 'CCU', 2.25), ('CCU', 'DEL', 2.25),
            ('BOM', 'MAA', 2.0), ('MAA', 'BOM', 2.0),
            ('DEL', 'HYD', 2.0), ('HYD', 'DEL', 2.0),
            ('BLR', 'GOI', 1.25), ('GOI', 'BLR', 1.25),
            ('DEL', 'JAI', 1.0), ('JAI', 'DEL', 1.0),
            ('BOM', 'GOI', 1.0), ('GOI', 'BOM', 1.0),
            ('HYD', 'COK', 1.75), ('COK', 'HYD', 1.75),
        ]

        base_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        flight_count = 0
        for day_offset in range(7):  # Create flights for next 7 days
            flight_date = base_date + timedelta(days=day_offset)

            for origin_code, dest_code, duration_hours in routes:
                # Create 1-2 flights per route per day
                num_flights = random.randint(1, 2)
                for _ in range(num_flights):
                    hour = random.choice([6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21])
                    minute = random.choice([0, 15, 30, 45])

                    departure = flight_date.replace(hour=hour, minute=minute)
                    duration_minutes = int(duration_hours * 60)
                    arrival = departure + timedelta(minutes=duration_minutes)

                    airline = random.choice(airlines)
                    prefix = {'SkyWay Airlines': 'SW', 'IndiGo': '6E', 'Air India': 'AI', 'SpiceJet': 'SG', 'Vistara': 'UK'}
                    flight_num = f"{prefix[airline]}-{random.randint(100, 999)}"

                    base_economy = random.randint(3000, 8000)
                    economy_price = round(base_economy / 100) * 100  # Round to nearest 100

                    Flight.objects.create(
                        flight_number=flight_num,
                        airline=airline,
                        origin=airports[origin_code],
                        destination=airports[dest_code],
                        departure_time=departure,
                        arrival_time=arrival,
                        economy_price=economy_price,
                        business_price=economy_price * 2.5,
                        total_economy_seats=random.choice([120, 150, 180]),
                        total_business_seats=random.choice([20, 24, 30]),
                    )
                    flight_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {len(airports_data)} airports and {flight_count} flights!'))
