# CivicPulse - Citizen Grievance Management Portal

A full-stack web application for managing citizen grievances with AI-powered issue detection.

## Features

- **User Authentication**: Register, login, logout with role-based access control
- **Three User Roles**: Citizen, Officer, Admin
- **Complaint Management**: Submit, track, and resolve complaints
- **AI Image Detection**: Automatic issue detection from uploaded images
- **Map Integration**: GPS location selection using OpenStreetMap
- **Real-time Status Updates**: Track complaint progress through status timeline
- **Admin Dashboard**: System analytics and user management
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Django 4.2+
- **Database**: SQLite (default) / MySQL (optional)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI/ML**: PyTorch, OpenCV
- **Maps**: Leaflet.js with OpenStreetMap

## Installation

### Prerequisites

- Python 3.10+
- pip or uv package manager

### Setup

1. **Clone or download the project**

2. **Create virtual environment**
   ```bash
   cd django_project
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations app
   python manage.py migrate
   ```

5. **Create superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Create media directories**
   ```bash
   mkdir -p media/complaints
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
django_project/
├── manage.py
├── requirements.txt
├── grievance_portal/          # Project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── app/                       # Main application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── ai_detection.py
├── templates/                 # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── auth/
│   ├── citizen/
│   ├── officer/
│   └── admin/
├── static/                    # Static files
│   ├── css/
│   ├── js/
│   └── images/
└── media/                     # User uploads
    └── complaints/
```

## User Roles

### Citizen
- Submit complaints with photos and location
- Track complaint status
- View complaint history
- Submit feedback after resolution

### Officer
- View assigned complaints
- Update complaint status
- Add remarks to complaints
- Mark complaints as resolved

### Admin
- View all complaints and statistics
- Assign officers to complaints
- Manage users and roles
- System analytics dashboard

## Creating Test Users

After creating the superuser, you can create test users:

1. Login to Django admin: http://127.0.0.1:8000/admin/
2. Go to Users and create new users
3. Set their role to 'citizen' or 'officer'

Or create users programmatically:
```python
python manage.py shell

from app.models import User

# Create a citizen
citizen = User.objects.create_user(
    email='citizen@example.com',
    password='password123',
    name='John Citizen',
    role='citizen'
)

# Create an officer
officer = User.objects.create_user(
    email='officer@example.com',
    password='password123',
    name='Jane Officer',
    role='officer'
)
```

## AI Detection (Optional)

The AI detection feature requires PyTorch and OpenCV. If not installed, the system will use simulated detection.

To enable full AI detection:
```bash
pip install torch torchvision opencv-python
```

For production, you would train a custom model on civic issue images.

## Configuration

### Email Notifications

Edit `grievance_portal/settings.py` to configure email:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### MySQL Database (Optional)

1. Install MySQL client:
   ```bash
   pip install mysqlclient
   ```

2. Update `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'grievance_db',
           'USER': 'your_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

## License

This project is for educational purposes.
