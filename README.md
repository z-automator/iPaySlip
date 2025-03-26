# iPayslip

A comprehensive payroll management system built with Django that supports employee management, payroll processing, loan management with automatic deductions, payslip generation, and role-based access control.

## Features

- **Employee Management**: Add, edit, and manage employee information
- **Payroll Processing**: Generate and manage payroll records with automatic calculations
- **Tax Calculation**: Tiered tax calculation based on configurable tax brackets
- **Loan Management**: Track employee loans and automatic deductions from payroll
- **Payslip Generation**: Generate professional PDF payslips for employees
- **Role-Based Access Control**: Secure access based on user roles and permissions

## Technology Stack

- Django 4.2+
- PostgreSQL (Supabase)
- Redis (for caching and Celery)
- Bootstrap 5 (UI)
- ReportLab/xhtml2pdf (PDF generation)
- Celery (scheduled tasks)
- Nginx (production server)
- Gunicorn (WSGI server)

## Prerequisites

- Python 3.11+
- PostgreSQL or Supabase account
- Redis server (for production)
- Email service account (e.g., Gmail)

## Installation & Setup

### Option 1: Using the Run Script (Recommended)

The project includes a convenient `run.py` script that handles all the setup and running of the application:

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   # Development mode (default)
   python run.py

   # Production mode
   python run.py --env prod
   ```

The script will:
- Check for required dependencies
- Set up environment variables from .env.example if .env doesn't exist
- Create necessary directories
- Run database migrations
- Collect static files
- Start the appropriate server (development or production)

### Option 2: Manual Setup

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy `.env.example` to `.env` for development or `.env.prod` for production
   - Update the variables with your values:
     ```
     # Database (Supabase)
     DATABASE_URL=your-supabase-connection-url
     DATABASE_SSL_MODE=require

     # Redis (if using)
     REDIS_URL=redis://localhost:6379/1
     
     # Email
     EMAIL_HOST_USER=your-email@gmail.com
     EMAIL_HOST_PASSWORD=your-app-specific-password
     ```

4. **Initialize the database**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```bash
   # Development
   python manage.py runserver

   # Production
   python manage.py collectstatic
   gunicorn payslip.wsgi_prod:application --bind 0.0.0.0:8000 --workers 3
   ```

6. **Start Celery (optional, for background tasks)**:
   ```bash
   # Start Redis first if not running
   redis-server

   # Start Celery worker
   celery -A payslip worker -l info

   # Start Celery beat (for scheduled tasks)
   celery -A payslip beat -l info
   ```

### Option 3: Docker Deployment

1. **Set up environment variables**:
   - Copy `.env.prod.example` to `.env.prod`
   - Update the variables with your production values

2. **Build and start the containers**:
   ```bash
   # Development
   docker-compose up --build

   # Production
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Run migrations and create superuser**:
   ```bash
   # Development
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser

   # Production
   docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
   docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

## Development Setup

1. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Run tests**:
   ```bash
   python manage.py test
   ```

## Production Deployment Checklist

1. **Update production settings**:
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`
   - Set up proper email backend
   - Configure SSL/HTTPS settings

2. **Set up SSL certificate**:
   - Obtain SSL certificate (e.g., Let's Encrypt)
   - Update Nginx configuration
   - Enable HTTPS redirects

3. **Configure backups**:
   - Set up database backups
   - Configure media files backup
   - Test restore procedures

4. **Set up monitoring**:
   - Configure error logging
   - Set up performance monitoring
   - Configure alert notifications

## Project Structure

```
payslip/
├── core/           # Core functionality
├── employees/      # Employee management
├── payroll/        # Payroll processing
├── lending/        # Loan management
├── templates/      # HTML templates
├── static/         # Static files
├── media/         # User-uploaded files
└── payslip/       # Project settings
```

## API Documentation

API documentation is available at `/api/docs/` when running the server.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@yourdomain.com or create an issue in the repository.