# 🤖 ML-Project Backend API

This repository contains the Flask backend for a system designed to detect and manage environmental issues (specifically **potholes** and **waste**) using machine learning models. 

## 🚀 Project Setup

Follow these steps to get a local copy of the project running on your machine.

### Prerequisites

You'll need the following installed:

* **Python 3.8+**
* **PostgreSQL Database** (running locally or remotely)
* **Git**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SmartCity
```
### 2. Set up Virtual Environment
Create and activate a virtual environment to manage dependencies.
```
create- python -m venv venv
activate- .\venv\Scripts\activate
```
### . Install Dependencies
Install all required Python packages from the requirements.txt file:

```bash
pip install -r requirements.txt
```
### 4. Configuration
Update the config.py file with your own database and security keys.

## Key Configuration Variables:
```python
class Config:
    # 🔑 IMPORTANT: Update this with your actual PostgreSQL connection string.
    SQLALCHEMY_DATABASE_URI = 'postgresql://<user>:<password>@<host>:<port>/<db_name>'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 🔐 CRITICAL: Change this to a long, random secret key for security.
    SECRET_KEY = 'YOUR_SUPER_SECRET_KEY'
    
    # Path where detection images are stored
    DETECTION_IMAGE_FOLDER = 'storage/uploads'
  
```
### 🐘 Database Management (Migrations)
This project uses Flask-Migrate to handle database changes.

## 1.Initialize Migration Repository (Run only once):
```bash
flask db init
```
## 2.Create Initial Migration Script:
```bash
flask db migrate -m "Initial database setup"
```
## 3. Apply Migrations to DB:
```bash
flask db upgrade
```
###  Running the Application
Ensure your virtual environment is active, and then run the main application file:

```bash
python app.py
```
The server will start running, typically accessible at http://127.0.0.1:5000/.

### 🗺️ API Endpoints Reference
All endpoints prefixed with /api/detections/ and /auth/ are available.


## 🔑 Authentication Routes (`/auth`) for both oganization and uesrs

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/auth/register` | Register a new user or organization. | No |
| **`POST`** | `/auth/login` | Login for user or organization, returns JWT token. | No |
| **`GET`** | `/auth/profile` | Retrieves the authenticated user's details. | Yes |

## 🏢 Organization Routes

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **`GET`** | `/api/detections/my` | Get all detections assigned to the logged-in organization. | Yes |

## 👤 User Routes (`/api/detections`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/api/detections/create` | Uploads, runs ML, and saves the detection record. | Yes |
| **`GET`** | `/api/detections/my` | Get all detections submitted by the current user. | Yes |
| **`GET`** | `/api/detections/type/<detection_type>` | Get all detections of a specific type (e.g., pothole). | Yes |
| **`GET`** | `/api/detections/user/<user_uuid>` | Get all detections for a specific user by UUID. | Yes |
| **`GET`** | `/api/detections/my/<detection_id>` | Get a single detection record by ID. | Yes |
| **`DELETE`**| `/api/detections/my/delete/<detection_id>` | Delete a single detection record by detection ID. | Yes |

## 🧠 ML Inference Route (`/detection`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/detection/detects` | Run ML detection on an uploaded image. | No |
