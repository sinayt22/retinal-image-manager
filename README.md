# Patient Management System

A comprehensive web application for managing patient data, medical images, clinical sites, and AI readiness assessment.

## Overview

This system helps healthcare professionals manage patient records and associated medical images. It includes features for tracking image quality and anatomy scores, providing insights into AI readiness of patient data across different collection sites.

### Features

- **Patient Management**: Create, view, update, and delete patient records
- **Image Management**: Upload, categorize, and assess quality of medical images
- **Site Management**: Track different clinical sites where images are collected
- **AI Readiness Dashboard**: Visualize data quality and assess readiness for AI processing
- **Data Validation**: Ensure data integrity with comprehensive validation

## Technology Stack

- **Backend**: Python 3.10, Flask 3.1.0
- **Database**: SQLAlchemy ORM with migration support via Alembic
- **Frontend**: Bootstrap 5, Chart.js for data visualization
- **Testing**: pytest with coverage reporting
- **Containerization**: Docker and Docker Compose

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

#### Local Setup

1. Clone the repository
```bash
git clone <repository-url>
cd retinal-image-manager
```

2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///app.db
UPLOAD_FOLDER=uploads/images
```

5. Initialize the database
```bash
flask db upgrade
```

6. Run the application
```bash
flask run
```

The application will be available at http://localhost:5000

#### Docker Setup

1. Clone the repository and navigate to the project directory

2. Create a `.env` file as described above

3. Build and start the containers
```bash
docker-compose up -d
```

The application will be available at http://localhost:5000

### Testing
Install the test requirements:
```bash
pip install -r tests/test_requirements.txt
```

Run the test suite with coverage reporting:

```bash
# Local setup
python -m pytest --cov=app tests/

# Using Docker
docker-compose run test
```

## Data Import

The system includes a script for importing test data:

```bash
# Local setup
python scripts/import_script.py --randomize --num-sites 10 --num-patients 50

# Using Docker
docker-compose run import
```

Options:
- `--randomize`: Randomize image quality, anatomy scores, and site values
- `--num-sites`: Number of sites to generate (default: 5)
- `--num-patients`: Number of patients to generate if there aren't enough (default: 0)
- `--max-images-per-patient`: Maximum number of images per patient (default: 4)

## Project Structure

```
.
├── app/                    # Application package
│   ├── controllers/        # Route handlers and business logic
│   ├── models/             # Database models
│   ├── services/           # Service layer
│   ├── templates/          # Jinja2 templates
│   ├── __init__.py         # Application factory
│   └── config.py           # Configuration
├── migrations/             # Database migrations
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── uploads/                # Image storage directory
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
└── docker-compose.yml      # Docker Compose configuration
```

## Dashboard

The application includes an AI readiness dashboard that visualizes:

- Patient data quality across different sites
- Image quality distribution
- Anatomy score distribution
- Illumination analysis
- Overall readiness statistics

Access the dashboard at http://localhost:5000/dashboard

## Database Schema

### Patients
- `id`: Primary key
- `birth_date`: Patient date of birth
- `sex`: Enumerated value (MALE/FEMALE/OTHER)
- `created_at`: Record creation timestamp
- `modified_at`: Record update timestamp

### Images
- `id`: Primary key
- `patient_id`: Foreign key to patients
- `eye_side`: Enumerated value (LEFT/RIGHT)
- `quality_score`: Enumerated value (LOW/ACCEPTABLE/HIGH)
- `anatomy_score`: Enumerated value (POOR/ACCEPTABLE/GOOD)
- `site_id`: Foreign key to sites
- `over_illuminated`: Boolean flag
- `image_path`: Path to stored image
- `acquisition_date`: Image capture date
- `created_at`: Record creation timestamp
- `modified_at`: Record update timestamp

### Sites
- `id`: Primary key
- `name`: Site name (unique)
- `location`: Site geographic location
- `created_at`: Record creation timestamp
- `modified_at`: Record update timestamp

# Technology Choices and Future Improvements

## Current Design Choices
I chose to use flask, sqlite and local file storage as the tech stack for this app, to build a prototype and test workflows.
I aimed for faster development and simplicity with minimal infrastructure setup over other non functional requirements (which are not defined at this stage).
I chose SQL db over NoSQL since since we're dealing with medical data, which suggests that consistency and ACID compliance ranks high for this application. 
In addition, joins between tables are used often in this application, so SQL feels like a natural choice over other NoSQL dbs.  

## Future Improvements
For future improvement and scale I would consider the following:

### Storage
- Switch from sqlite to PostgresSQL or another SQL DB fit more to scale (as sqlite doesn't scale well).
- Add another DB to store data (perhaps the statistics data) that is more readily available for AI model training (if applicable).
- Use object storage for the images (e.g. AWS S3) for scalablility and avoid storing the files locally.

### Backend
Several options exists:
- Can convert the flask application to serve only as API server, and convert the controllers serve API endpoints instead of templates.
- Switch to FastAPI - alternative to flask with perhaps better performace.
- Can switch to use Djano if we need more admin capabilities and other web related utilites.

### Frontend
- Once we update our backend to use API endpoint, we can migrate from server rendered pages to modern SPA frameworks (React, Angular, Vue)

## Further Considerations
- **Compliance** - Compliance to regulation regarding patient data
- **Security** - Authentication and Authorization, Data Encryption
- **Performace** - Quality Assessment and Upload as separate steps in a queue
- **AI Integration** - Api endpoints for model training data extraction
- **Backup and Recovery** - Data replication, Redundancy, Recovery Plan