# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Unregister from activities
- Persist activity and participant data using SQLite

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses a SQLite database (`src/data/activities.db`) with a simple schema:

1. **activities**

   - `id` (primary key)
   - `name` (unique)
   - Description
   - Schedule
   - Maximum number of participants allowed

2. **activity_participants**

   - `(activity_id, email)` composite primary key
   - Stores which students are signed up for each activity

On first run, the database is initialized and seeded with default activities.

## Persistence Notes

- Data now survives server restarts.
- To reset to a fresh seeded dataset, delete `src/data/activities.db` and restart the app.

