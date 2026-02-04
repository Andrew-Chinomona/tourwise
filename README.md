# TourWise

A modern property listing platform built with Django, featuring real-time property search, interactive maps, and a streamlined property submission process.

## Features

### Core Functionality
- **Single-Page Property Submission**: Streamlined form for adding property listings with all details in one place
- **Interactive Maps**: Location selection and display using Leaflet.js and OpenStreetMap
- **Free Location Autocomplete**: Nominatim-powered address search (no API keys required)
- **Multi-Currency Support**: List properties in ZWL, USD, EUR, GBP, or ZAR
- **Property Amenities**: Extensive amenity selection with icons
- **Image Galleries**: Multiple property images with main image showcase
- **Search & Filter**: Advanced property search by location, type, and price
- **User Dashboards**: Separate dashboards for hosts and tenants
- **Payment Integration**: PayNow payment gateway for property listings

### Technical Highlights
- **GeoDjango**: PostGIS spatial database for location-based queries
- **Cloud Database**: Neon Postgres serverless database
- **RESTful API**: Django REST Framework for property data
- **Responsive Design**: Bootstrap 5 for mobile-friendly interface
- **Draft System**: Save property listings as drafts before payment

## Tech Stack

- **Backend**: Django 5.2, Python 3.13
- **Database**: PostgreSQL (Neon) with PostGIS extension
- **Frontend**: Bootstrap 5, Leaflet.js, Nominatim
- **Payment**: PayNow Integration
- **Deployment Ready**: Environment-based configuration

## Prerequisites

- Python 3.13+
- PostgreSQL with PostGIS (or Neon account)
- Conda (recommended) or pip
- Git

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/tourwise.git
cd tourwise
```

### 2. Set Up Environment

#### Using Conda (Recommended)
```bash
conda create -n tourwise-env python=3.13
conda activate tourwise-env
```

#### Using venv
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Django Secret Key
SECRET_KEY=your-secret-key-here

# Debug Mode (set to False in production)
DEBUG=True

# Neon Postgres Database
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# API Keys
GROQ_API_KEY=your-groq-api-key-here

# PayNow Configuration
PAYNOW_INTEGRATION_ID=your-integration-id
PAYNOW_INTEGRATION_KEY=your-integration-key
PAYNOW_MODE=test  # or 'live' for production
```

### 5. Set Up Database

#### Load Initial Data (Currencies & Amenities)
Use the Neon SQL Editor to run the seed data:
```bash
# Copy the SQL file content to Neon Console
cat load_currencies_amenities.sql
```

Or use the Python script:
```bash
python load_data.py
```

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## Running the Application

### Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

### Admin Panel
Access the Django admin at `http://127.0.0.1:8000/admin/`

## Project Structure

```
tourwise/
├── accounts/              # User authentication and profiles
│   ├── templates/         # Login, signup, dashboards
│   └── views.py          # User-related views
├── listings/              # Property listings
│   ├── templates/         # Property forms and details
│   ├── models.py         # Property, Currency, Amenity models
│   ├── forms.py          # PropertyListingForm
│   ├── views.py          # CRUD operations
│   └── api_views.py      # REST API endpoints
├── payments/              # PayNow integration
│   ├── models.py         # Payment records
│   └── views.py          # Payment processing
├── static/
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript (Nominatim, maps)
│   └── images/           # Static images
├── media/                # User-uploaded images
├── tourwise_website/     # Django project settings
│   ├── settings.py       # Configuration
│   └── urls.py           # URL routing
├── .env                  # Environment variables (not in repo)
├── .gitignore           # Git ignore patterns
├── requirements.txt     # Python dependencies
└── manage.py            # Django management script
```

## Key Models

### Property
- Property type, description, location (PostGIS Point)
- Pricing with multi-currency support
- Bedrooms, bathrooms, area
- Contact information
- Main image and gallery
- Amenities (many-to-many)
- Draft/published status

### Currency
- Code (ZWL, USD, EUR, GBP, ZAR)
- Name and symbol

### Amenity
- Name and Font Awesome icon
- Examples: WiFi, Parking, Pool, Security

## API Endpoints

### Properties API
- `GET /listings/properties/` - List all published properties
- `GET /listings/properties/{id}/` - Property details
- `GET /listings/api/locations/` - Location suggestions for autocomplete

## Features in Detail

### Property Submission Flow
1. User logs in as a host
2. Navigates to "Add Property"
3. Fills out single-page form with:
   - Property type and description
   - Location (with map picker)
   - Main image and interior images
   - Price and currency
   - Amenities
   - Contact information
   - Property details (bedrooms, bathrooms, area)
4. Saves as draft or proceeds to payment
5. Property goes live after payment confirmation

### Location Autocomplete
- Powered by Nominatim (OpenStreetMap)
- No API key required
- Country-specific search (Zimbabwe default)
- Returns formatted addresses with coordinates
- Interactive map marker placement

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (True/False) | Yes |
| `DATABASE_URL` | Neon Postgres connection string | Yes |
| `GROQ_API_KEY` | GROQ API key | Optional |
| `PAYNOW_INTEGRATION_ID` | PayNow merchant ID | Yes |
| `PAYNOW_INTEGRATION_KEY` | PayNow secret key | Yes |
| `PAYNOW_MODE` | test or live | Yes |

## Database Schema

### PostGIS Extensions
The project uses PostGIS for geospatial queries:
- Location stored as `Point` (longitude, latitude)
- Distance-based property searches
- Map boundary queries

## Development Notes

### Neon Database
This project uses Neon serverless Postgres with:
- Connection pooling enabled
- PostGIS extension for spatial queries
- SSL required for connections

### OneDrive Users
If using OneDrive for file storage, pause sync during git operations to avoid file locking issues.

### GDAL/GEOS Requirements
GeoDjango requires GDAL and GEOS libraries. On Windows with Conda:
```bash
conda install -c conda-forge gdal geos
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenStreetMap & Nominatim for free geocoding
- Leaflet.js for interactive maps
- Django community for excellent documentation
- Neon for serverless Postgres hosting

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review Django and GeoDjango documentation

## Changelog

### Version 2.0 (Latest)
- Refactored to single-page property submission form
- Migrated from local PostgreSQL to Neon Postgres
- Replaced Google Maps API with Nominatim (free)
- Added Currency and Amenity models
- Removed chatbot functionality
- Cleaned up legacy multi-step form code

### Version 1.0
- Initial release with 10-step property submission wizard
- Local PostgreSQL database
- Google Maps integration
- Basic property listings and search
