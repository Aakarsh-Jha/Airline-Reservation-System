# Manipal Airlines Reservation System

<div align="center">
  <img src="https://img.shields.io/badge/Framework-Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Frontend-Vanilla_JS_%26_CSS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="Vanilla JS">
</div>

<br/>

## Overview
**Manipal Airlines** is a premium, boutique-style airline reservation system built with Django. It features a highly refined charcoal and amber color palette, editorial-grade typography, and boarding-pass-inspired UI components. The platform offers a cohesive, high-end user experience, combining rich visual design with advanced interactive features like dynamic geospatial mapping, intelligent price prediction, and real-time interactive seat selection.

## ✨ Key Features

- **Sophisticated Boutique Design**: A departure from generic themes. It features a bespoke charcoal and amber aesthetic with glassmorphic elements and smooth micro-animations.
- **Interactive Seat Selection**: A responsive, visual seat map allowing users to pinpoint their exact seats. It strictly enforces selection rules based on the number of passengers, class capacity (Economy/Business), and existing bookings.
- **Geospatial Route Mapping**: Integration with **Leaflet.js** to provide beautiful, interactive visualizations of flight paths, originating cities, destinations, and layovers.
- **Dynamic Price Prediction**: **Chart.js** powered price trends that simulate 7-day price histories and provide smart booking recommendations (*"Book Now"*, *"Wait"*, or *"Good Time to Book"*).
- **Boarding-Pass UI**: Flight search results and booking confirmations are displayed as elegant, realistic digital boarding passes.
- **Comprehensive Booking Lifecycle**: Full user flow from flight search, class selection, passenger detail entry, to a dedicated **"My Bookings"** dashboard for managing flights.
- **User Authentication**: Secure robust registration, login, and profile management capabilities.

## 🛠️ Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML5, Vanilla CSS, Vanilla JavaScript
- **Database:** SQLite (default)
- **Data Visualization & Mapping:** Leaflet.js, Chart.js

## 📂 Project Structure

```text
.
├── airline_project/       # Main Django configuration & settings
├── flights/               # Core application logic
│   ├── models.py          # Database schemas (Flight, Airport, Booking, UserProfile)
│   ├── views.py           # Core business logic & request handling
│   ├── forms.py           # Django forms (Search, Booking, Auth)
│   └── templates/         # HTML templates with injected dynamic JS
├── static/                # Custom styling (CSS) and interactivity (JS)
├── db.sqlite3             # Local database
└── manage.py              # Django execution script
```

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.8+** installed on your system.

### Instructions

1. **Navigate to the core project directory:**
   ```bash
   cd "Manipal Airlines"
   ```

2. **Install necessary dependencies:**
   Since this project uses vanilla Django, install it via pip:
   ```bash
   pip install django
   ```

3. **Apply database migrations:**
   Prepare the SQLite database by running:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser (Admin) — *Optional*:**
   To access the Django Admin panel (`/admin/`) to add Airports and Flights:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   Open your preferred web browser and navigate to:
   **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**


