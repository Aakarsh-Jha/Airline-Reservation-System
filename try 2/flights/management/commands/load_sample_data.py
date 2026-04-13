from django.core.management.base import BaseCommand
from django.utils import timezone
from flights.models import Airport, Flight
from datetime import timedelta
import random
import json


class Command(BaseCommand):
    help = 'Load sample airports and flights data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating airports...')

        # (code, name, city, latitude, longitude)
        airports_data = [
            ('DEL', 'Indira Gandhi International Airport', 'Delhi', 28.5562, 77.1000),
            ('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai', 19.0896, 72.8656),
            ('BLR', 'Kempegowda International Airport', 'Bengaluru', 13.1986, 77.7066),
            ('MAA', 'Chennai International Airport', 'Chennai', 12.9941, 80.1709),
            ('CCU', 'Netaji Subhas Chandra Bose International Airport', 'Kolkata', 22.6547, 88.4467),
            ('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad', 17.2403, 78.4294),
            ('COK', 'Cochin International Airport', 'Kochi', 10.1520, 76.4019),
            ('GOI', 'Goa International Airport', 'Goa', 15.3808, 73.8314),
            ('JAI', 'Jaipur International Airport', 'Jaipur', 26.8242, 75.8122),
            ('AMD', 'Sardar Vallabhbhai Patel International Airport', 'Ahmedabad', 23.0225, 72.5714),
        ]

        airports = {}
        for code, name, city, lat, lng in airports_data:
            airport, created = Airport.objects.update_or_create(
                code=code,
                defaults={
                    'name': name, 'city': city, 'country': 'India',
                    'latitude': lat, 'longitude': lng
                }
            )
            airports[code] = airport
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {airport}')

        self.stdout.write('\nCreating flights...')

        # Delete old flights to avoid duplicates on re-run
        Flight.objects.all().delete()

        airlines = ['Manipal Airlines', 'IndiGo', 'Air India', 'SpiceJet', 'Vistara']

        # Direct (non-stop) routes: (origin, dest, duration_hours)
        direct_routes = [
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

        # Routes with layovers: (origin, dest, stops_list, total_duration_hours)
        layover_routes = [
            ('DEL', 'COK', ['BOM'], 4.5),
            ('COK', 'DEL', ['BOM'], 4.5),
            ('DEL', 'GOI', ['AMD'], 3.5),
            ('GOI', 'DEL', ['AMD'], 3.5),
            ('CCU', 'BOM', ['HYD'], 4.0),
            ('BOM', 'CCU', ['HYD'], 4.0),
            ('DEL', 'MAA', ['HYD'], 4.5),
            ('MAA', 'DEL', ['HYD'], 4.5),
            ('CCU', 'BLR', ['HYD'], 4.25),
            ('BLR', 'CCU', ['HYD'], 4.25),
            ('JAI', 'BLR', ['BOM'], 5.0),
            ('BLR', 'JAI', ['BOM'], 5.0),
            ('DEL', 'COK', ['HYD', 'BLR'], 6.5),
            ('COK', 'DEL', ['BLR', 'HYD'], 6.5),
            ('CCU', 'GOI', ['HYD', 'BOM'], 6.0),
            ('GOI', 'CCU', ['BOM', 'HYD'], 6.0),
        ]

        base_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        flight_count = 0
        for day_offset in range(7):  # Create flights for next 7 days
            flight_date = base_date + timedelta(days=day_offset)

            # Direct flights
            for origin_code, dest_code, duration_hours in direct_routes:
                num_flights = random.randint(1, 2)
                for _ in range(num_flights):
                    hour = random.choice([6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21])
                    minute = random.choice([0, 15, 30, 45])

                    departure = flight_date.replace(hour=hour, minute=minute)
                    duration_minutes = int(duration_hours * 60)
                    arrival = departure + timedelta(minutes=duration_minutes)

                    airline = random.choice(airlines)
                    prefix = {'Manipal Airlines': 'SW', 'IndiGo': '6E', 'Air India': 'AI', 'SpiceJet': 'SG', 'Vistara': 'UK'}
                    flight_num = f"{prefix[airline]}-{random.randint(100, 999)}"

                    base_economy = random.randint(3000, 8000)
                    economy_price = round(base_economy / 100) * 100

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
                        stops='[]',
                    )
                    flight_count += 1

            # Flights with layovers (1 per route per day)
            for origin_code, dest_code, stop_codes, duration_hours in layover_routes:
                hour = random.choice([6, 7, 8, 9, 10, 11])
                minute = random.choice([0, 15, 30, 45])

                departure = flight_date.replace(hour=hour, minute=minute)
                duration_minutes = int(duration_hours * 60)
                arrival = departure + timedelta(minutes=duration_minutes)

                airline = random.choice(airlines)
                prefix = {'Manipal Airlines': 'SW', 'IndiGo': '6E', 'Air India': 'AI', 'SpiceJet': 'SG', 'Vistara': 'UK'}
                flight_num = f"{prefix[airline]}-{random.randint(100, 999)}"

                base_economy = random.randint(2500, 5500)
                economy_price = round(base_economy / 100) * 100

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
                    stops=json.dumps(stop_codes),
                )
                flight_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {len(airports_data)} airports and {flight_count} flights!'))
        self.stdout.write(f'  Direct flights + {len(layover_routes)} layover routes per day')
