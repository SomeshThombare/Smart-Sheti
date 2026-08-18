# 🌱 Smart Sheti — AI BASED SMART FARMING SUPPORT PLATFORM

Smart Sheti is an AI-powered agriculture platform designed to help farmers make better farming decisions using machine learning, crop analysis, disease detection, pest detection, fertilizer recommendations, weather information, government schemes, and an AI chatbot.

The application is built using **Python and Django** with multiple independent Django modules and integrated machine-learning models.

---

# 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [Main Features](#-main-features)
3. [Technology Stack](#-technology-stack)
4. [Project Architecture](#-project-architecture)
5. [Django Modules](#-django-modules)
6. [AI/ML Models](#-aiml-models)
7. [Datasets](#-datasets)
8. [Model Files](#-model-files)
9. [Project Structure](#-project-structure)
10. [System Requirements](#-system-requirements)
11. [Installation](#-installation)
12. [Environment Variables](#-environment-variables)
13. [Database Setup](#-database-setup)
14. [Run the Project](#-run-the-project)
15. [AI Model Setup](#-ai-model-setup)
16. [Git LFS](#-git-lfs)
17. [Disease Detection Workflow](#-disease-detection-workflow)
18. [Pest Detection Workflow](#-pest-detection-workflow)
19. [Fertilizer Recommendation Workflow](#-fertilizer-recommendation-workflow)
20. [Crop Prediction Workflow](#-crop-prediction-workflow)
21. [Troubleshooting](#-troubleshooting)
22. [Important Notes](#-important-notes)

---

# 🌾 Project Overview

Smart Sheti provides a centralized platform where a farmer can:

* Register and log in
* Manage crop information
* View a farmer dashboard
* Detect crop diseases from leaf images
* Detect crop pests
* Get fertilizer recommendations
* Get crop-related predictions/advice
* View weather information
* Access government agricultural schemes
* Use an AI chatbot
* Maintain prediction/history records

The project uses Django as the backend and provides both HTML-based interfaces and REST-style API endpoints.

The disease-detection module, for example, supports authenticated farmer image uploads and stores prediction information such as crop name, disease, confidence, treatment, suggestion, status, and timestamp.

---

# 🚀 Main Features

## 1. Authentication

The `accounts` application manages:

* Farmer registration
* Login
* OTP verification
* Forgot password
* Password reset
* Profile management
* Admin management
* Authentication and authorization

The project also uses role-based access for farmer and admin users.

---

## 2. Farmer Dashboard

The dashboard provides a central interface for farmers to access the major Smart Sheti services.

Main areas include:

* Crop information
* Disease detection
* Pest detection
* Fertilizer recommendation
* Weather
* Government schemes
* AI chatbot
* Farming information

---

## 3. Crop Management

The `crop` application manages crop-related information and prediction records.

It contains:

```text
crop/
├── migrations/
├── ml/
│   ├── accuracy.txt
│   ├── classification_report.json
│   └── crop_model.pkl
├── templates/
├── crop_advice.py
├── forms.py
├── ml_model.py
├── models.py
├── train_model.py
├── urls.py
└── views.py
```

The trained crop model is stored as:

```text
crop/ml/crop_model.pkl
```

---

# 🤖 AI/ML Models

Smart Sheti contains multiple AI/ML components.

## Model 1 — Crop Disease Detection

### Algorithm

**EfficientNet-B0 CNN**

The disease detection model uses:

```text
EfficientNet-B0
        ↓
Global Average Pooling
        ↓
Batch Normalization
        ↓
Dropout
        ↓
Dense Softmax Classifier
```

The implementation uses ImageNet-pretrained EfficientNet-B0 and performs transfer learning.

The base model is initially frozen and the classifier head is trained. A second fine-tuning stage makes the later EfficientNet layers trainable.

### Input

Crop/leaf image.

The image is resized to:

```text
224 × 224 pixels
```

### Output

The model predicts:

* Crop name
* Disease name
* Confidence score
* Class name
* Predicted class index
* Treatment
* Farming suggestion

The inference code uses the model prediction and selects the class using `argmax`.

### Disease classes

The current `class_names.json` contains 18 classes:

```text
Corn - Common Rust
Corn - Gray Leaf Spot
Corn - Healthy
Corn - Northern Leaf Blight

Potato - Early Blight
Potato - Healthy
Potato - Late Blight

Rice - Brown Spot
Rice - Healthy
Rice - Leaf Blast
Rice - Neck Blast

Sugarcane - Bacterial Blight
Sugarcane - Healthy
Sugarcane - Red Rot

Wheat - Brown Rust
Wheat - Healthy
Wheat - Yellow Rust
```

### Dataset

The training script downloads:

```text
kamal01/top-agriculture-crop-disease
```

from Kaggle using `kagglehub`.

The training process automatically downloads and prepares the dataset.

### Training configuration

```text
Image size: 224 × 224
Batch size: 16
Stage 1 epochs: 10
Stage 2 epochs: 15
Random seed: 42
```

Data augmentation includes:

* Random horizontal flip
* Random rotation
* Random zoom
* Random contrast

### Training

Run:

```bash
python disease_detection/train_model.py
```

The training script downloads the dataset, prepares the training directory, creates training/validation datasets, trains the classifier, fine-tunes EfficientNet, and saves the model and class names.

---

# 🐛 Model 2 — Pest Detection

The project contains a separate `pest_detection` application.

Structure:

```text
pest_detection/
└── ai_model/
    ├── dataset/
    │   └── ip02_dataset/
    ├── models/
    │   ├── pest_class_names.json
    │   └── pest_model.keras
    ├── runs/
    ├── uploads/
    ├── download_dataset.py
    ├── predict_pest.py
    ├── solution.py
    ├── train_model.py
    └── yolov8n.pt
```

The repository contains:

```text
pest_model.keras
yolov8n.pt
pest_class_names.json
```

The training data is organized into:

```text
train/
val/
test/
```

The project also contains YOLO-related training assets and `yolov8n.pt`.

### Important

The actual dataset is intentionally not stored in Git because it is large.

The training/output directories are also excluded from the repository.

If you want to retrain the pest model, follow the dataset/download logic in:

```text
pest_detection/ai_model/download_dataset.py
pest_detection/ai_model/train_model.py
```

For normal application usage, use the already-trained model:

```text
pest_detection/ai_model/models/pest_model.keras
```

---

# 🧪 Model 3 — Fertilizer Recommendation

The fertilizer recommendation system is located in:

```text
ai_engine/
```

Important model files include:

```text
ai_engine/models/
├── feature_columns.pkl
├── fertilizer_classifier.pkl
├── label_encoder.pkl
└── quantity_regressor.pkl
```

The system uses trained machine-learning models to generate fertilizer recommendations based on agricultural/soil-related input features.

The serialized models include:

```text
fertilizer_classifier.pkl
quantity_regressor.pkl
label_encoder.pkl
feature_columns.pkl
```

### Why multiple files?

Each file has a different responsibility:

| File                        | Purpose                                                    |
| --------------------------- | ---------------------------------------------------------- |
| `fertilizer_classifier.pkl` | Fertilizer recommendation/classification model             |
| `quantity_regressor.pkl`    | Fertilizer quantity prediction                             |
| `label_encoder.pkl`         | Converts categorical labels to/from numeric representation |
| `feature_columns.pkl`       | Stores the feature structure expected by the model         |

### Important

The two large model files are stored using **Git LFS**:

```text
fertilizer_classifier.pkl
quantity_regressor.pkl
```

Therefore Git LFS must be installed before cloning/using the project.

---

# 🌱 Model 4 — Crop Prediction

The crop application contains:

```text
crop/ml/crop_model.pkl
```

along with:

```text
accuracy.txt
classification_report.json
```

These files contain the trained crop prediction model and its evaluation information.

The training source is:

```text
crop/train_model.py
```

The prediction/inference logic is handled through:

```text
crop/ml_model.py
```

### Important

The exact training algorithm and dataset should be taken from the current `crop/train_model.py` implementation if the model needs to be retrained.

Do not replace the trained model with a different algorithm without updating the prediction code.

---

# 💬 AI Chatbot

The chatbot module is:

```text
chatbot/
```

It contains:

```text
chatbot.py
services.py
views.py
serializers.py
urls.py
```

The chatbot provides an AI-based conversational interface for users.

API credentials must be stored in `.env`.

Never place API keys directly inside:

```text
settings.py
chatbot.py
services.py
```

---

# 🌦️ Weather Module

The weather application is:

```text
weather/
```

It contains:

```text
models.py
views.py
urls.py
```

Weather functionality requires the configured weather API credentials in the environment.

---

# 🏛️ Government Schemes

The:

```text
government_schemes/
```

application provides agricultural government-scheme functionality.

It includes separate:

* Farmer pages
* Admin pages
* Scheme listing
* Scheme detail
* Scheme management

---

# 🚜 Equipment Rental

The project also contains:

```text
equipment_rental/
```

This module provides equipment-management and booking functionality.

It contains:

* Equipment management
* Farmer equipment listing
* Booking
* Booking history
* Admin approval
* Payment-related pages

---

# 🛒 Marketplace

The project contains a:

```text
marketplace/
```

application for marketplace-related functionality.

---

# 🧑‍💻 Technology Stack

## Backend

```text
Python
Django
Django REST Framework
```

## Frontend

```text
HTML5
CSS3
JavaScript
Django Templates
```

## Database

The local development configuration can use:

```text
SQLite
```

The database file:

```text
db.sqlite3
```

is intentionally ignored by Git.

## Machine Learning

```text
TensorFlow
Keras
Scikit-learn
NumPy
Pillow
```

## Computer Vision

```text
OpenCV/PIL-related image processing
YOLO-related pest detection components
```

## APIs

The project uses external services for features such as:

```text
Weather API
AI chatbot API
Twilio
```

The exact API keys must be configured through environment variables.

---

# 📁 Project Structure

Main structure:

```text
smart_sheti/
│
├── accounts/
├── ai_engine/
├── chatbot/
├── crop/
├── dashboard/
├── disease_detection/
├── equipment_rental/
├── farmer/
├── fertilizer/
├── government_schemes/
├── marketplace/
├── pest_detection/
├── soil/
├── weather/
│
├── smart_sheti/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
└── .gitattributes
```

---

# 💻 System Requirements

Recommended environment:

```text
Windows / Linux / macOS
Python 3.x
Git
Git LFS
pip
Virtual Environment
```

Because TensorFlow and some ML packages are platform/version sensitive, use the versions specified in:

```text
requirements.txt
```

whenever possible.

---

# ⚙️ Installation on a New Machine

## Step 1 — Clone the repository

Install Git first.

Then:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Move into the project:

```bash
cd Smart-Sheti
```

---

# Step 2 — Install Git LFS

Git LFS is required because the repository contains large ML models.

Check:

```bash
git lfs version
```

If installed, initialize it:

```bash
git lfs install
```

Then download the LFS model files:

```bash
git lfs pull
```

Verify:

```bash
git lfs ls-files
```

You should see the large model files tracked by LFS.

---

# Step 3 — Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate:

```powershell
venv\Scripts\activate
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Step 4 — Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

# Step 5 — Install dependencies

Run:

```bash
pip install -r requirements.txt
```

Do not install random package versions if `requirements.txt` already specifies the required versions.

---

# 🔐 Environment Variables

The `.env` file is intentionally not included in Git.

Create:

```text
.env
```

in the project root.

Example:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

OPENWEATHER_API_KEY=your_weather_api_key

GEMINI_API_KEY=your_gemini_api_key

OPENROUTER_API_KEY=your_openrouter_api_key
```

Use the variable names actually referenced by the current source code.

### ⚠️ Never commit `.env`

The `.gitignore` contains:

```text
.env
```

Never put real API keys into:

```text
settings.py
README.md
GitHub
```

---

# 🗄️ Database Setup

After installing dependencies:

```bash
python manage.py makemigrations
```

Then:

```bash
python manage.py migrate
```

The repository already contains Django migration files for the applications.

For example, the disease detection module has migrations for the `DiseasePrediction` model.

---

# 👤 Create Admin User

Create a Django superuser:

```bash
python manage.py createsuperuser
```

Enter:

```text
Username
Email
Password
```

---

# ▶️ Run the Project

Start Django:

```bash
python manage.py runserver
```

The development server normally runs at:

```text
http://127.0.0.1:8000/
```

Open the address in your browser.

---

# 🧠 AI Model Setup

There are two ways to use the ML components.

## Option A — Use Existing Trained Models

Recommended.

Clone the repository and download Git LFS files:

```bash
git lfs install
git lfs pull
```

Then use the existing trained model files.

This avoids retraining large models.

---

# Option B — Retrain Models

Only retrain if you need to modify the model or dataset.

---

# 🦠 Disease Model Training

The training script is:

```text
disease_detection/train_model.py
```

Run:

```bash
python disease_detection/train_model.py
```

The script:

1. Downloads the dataset from Kaggle.
2. Copies/prepares the dataset.
3. Finds the training directory.
4. Creates TensorFlow datasets.
5. Splits the data into training and validation subsets.
6. Performs image augmentation.
7. Loads ImageNet-pretrained EfficientNet-B0.
8. Trains the classifier head.
9. Fine-tunes part of EfficientNet.
10. Saves the trained model.
11. Saves the class names.

---

# 🐛 Pest Model Training

Training code:

```text
pest_detection/ai_model/train_model.py
```

Dataset/download code:

```text
pest_detection/ai_model/download_dataset.py
```

The project contains:

```text
train/
val/
test/
```

dataset organization and YOLO-related files.

Before retraining, make sure the required dataset is available and the paths expected by `train_model.py` are correct.

---

# 🧪 Fertilizer Model

The trained fertilizer models are already stored as serialized files:

```text
ai_engine/models/
```

Do not retrain them unless you understand the feature preprocessing and model-input format.

The model requires the same feature structure used during training.

The following supporting files are therefore important:

```text
feature_columns.pkl
label_encoder.pkl
```

---

# 🌱 Crop Model

The trained model is:

```text
crop/ml/crop_model.pkl
```

Evaluation files:

```text
crop/ml/accuracy.txt
crop/ml/classification_report.json
```

Retraining script:

```text
crop/train_model.py
```

Inference:

```text
crop/ml_model.py
```

---

# 🔄 Disease Detection Workflow

The complete disease detection flow is:

```text
Farmer
   │
   ▼
Upload Crop Image
   │
   ▼
Django Form Validation
   │
   ▼
DiseasePrediction Record
   │
   ▼
Image Preprocessing
   │
   ├── Convert to RGB
   └── Resize to 224 × 224
   │
   ▼
EfficientNet-B0
   │
   ▼
Softmax Prediction
   │
   ▼
Highest Probability Class
   │
   ▼
Class Name
   │
   ├── Crop Name
   ├── Disease Name
   ├── Confidence
   ├── Treatment
   └── Suggestion
   │
   ▼
Save Prediction
   │
   ▼
Display Result
```

The disease module stores prediction history for the farmer.

---

# 🔄 Pest Detection Workflow

```text
Farmer
   │
   ▼
Upload Pest Image
   │
   ▼
Image Processing
   │
   ▼
Trained Pest Model
   │
   ▼
Pest Classification/Detection
   │
   ▼
Prediction Result
   │
   ▼
Save Result
   │
   ▼
Farmer History
```

---

# 🔄 Fertilizer Recommendation Workflow

```text
Farmer Input
    │
    ├── Soil/field parameters
    ├── Nutrient information
    └── Environmental information
    │
    ▼
Feature Preprocessing
    │
    ▼
Feature Columns
    │
    ▼
Fertilizer Classifier
    │
    ▼
Recommended Fertilizer
    │
    ▼
Quantity Regressor
    │
    ▼
Recommended Quantity
```

---

# 🔄 Crop Prediction Workflow

```text
Farmer Input
    │
    ▼
Feature Validation
    │
    ▼
Trained crop_model.pkl
    │
    ▼
Prediction
    │
    ▼
Crop Recommendation / Result
```

---

# 📦 Git LFS

Large model files are stored using Git LFS.

The repository tracks:

```text
ai_engine/models/fertilizer_classifier.pkl
pest_detection/ai_model/models/pest_model.keras
```

After cloning:

```bash
git lfs install
git lfs pull
```

Check:

```bash
git lfs ls-files
```

If an ML model appears as a very small pointer file instead of the real model, run:

```bash
git lfs pull
```

---

# 🚫 Files Not Included in Git

The following files/directories should not be committed:

```text
venv/
.venv/
__pycache__/
*.pyc
db.sqlite3
.env
media/
staticfiles/
.vscode/
.idea/
datasets/
runs/
uploads/
```

Datasets can be very large and should be downloaded separately when training is required.

---

# ⚠️ Important Disease Model Path Check

Before running disease detection, verify the model path.

The current inference code expects:

```text
disease_detection/crop_disease_model.keras
```

The project structure previously contained:

```text
disease_detection/disease_detection/crop_disease_model.h5
```

These paths/formats must be made consistent.

If the actual trained model is:

```text
crop_disease_model.h5
```

either:

1. Update the inference code to load the `.h5` file, or
2. Provide the `.keras` model at the path expected by the current code.

Do not simply rename a model file unless the saved model format and application code are compatible.

---

# 🛠️ Troubleshooting

## Problem: `No module named django`

Run:

```bash
pip install -r requirements.txt
```

Make sure the virtual environment is activated.

---

## Problem: `No module named rest_framework`

Install the dependency specified by the project's requirements:

```bash
pip install djangorestframework
```

Prefer using:

```bash
pip install -r requirements.txt
```

first.

---

## Problem: Model file not found

Check:

```bash
git lfs ls-files
```

Then:

```bash
git lfs pull
```

Verify the model path expected by the corresponding Python file.

---

## Problem: `.env` values are missing

Create:

```text
.env
```

and add the required environment variables.

Restart the Django server after changing environment configuration.

---

## Problem: Database tables do not exist

Run:

```bash
python manage.py migrate
```

---

## Problem: Static files are not loading

For development:

```bash
python manage.py runserver
```

For deployment, configure Django static files and run:

```bash
python manage.py collectstatic
```

---

## Problem: Dataset is missing

Datasets are intentionally excluded from Git.

For disease detection, the training script downloads:

```text
kamal01/top-agriculture-crop-disease
```

using `kagglehub`.

For pest detection, use the dataset/download logic provided inside:

```text
pest_detection/ai_model/
```

---

# 🔒 Security

Never commit:

```text
.env
API keys
Twilio credentials
Database passwords
Secret keys
Access tokens
```

Use environment variables.

Example:

```python
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
```

---

# 🧑‍💻 Developer Setup — Complete Command Sequence

For a completely new machine:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Smart-Sheti

git lfs install
git lfs pull

python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Then:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

# 🧪 Basic Verification Checklist

After setup, verify:

* [ ] Virtual environment activated
* [ ] Requirements installed
* [ ] `.env` created
* [ ] API keys configured
* [ ] Git LFS installed
* [ ] LFS models downloaded
* [ ] Database migrated
* [ ] Superuser created
* [ ] Django server starts
* [ ] Login works
* [ ] Farmer dashboard opens
* [ ] Disease detection loads
* [ ] Disease model loads
* [ ] Pest model loads
* [ ] Fertilizer recommendation loads
* [ ] Weather service works
* [ ] Chatbot API works

---

# 📚 Important Files

| File/Folder               | Purpose                             |
| ------------------------- | ----------------------------------- |
| `manage.py`               | Django command-line entry point     |
| `smart_sheti/settings.py` | Django configuration                |
| `smart_sheti/urls.py`     | Main URL configuration              |
| `requirements.txt`        | Python dependencies                 |
| `accounts/`               | Authentication and user management  |
| `dashboard/`              | Main dashboard                      |
| `crop/`                   | Crop management and prediction      |
| `disease_detection/`      | Crop disease detection              |
| `pest_detection/`         | Pest detection                      |
| `ai_engine/`              | ML/fertilizer engine                |
| `fertilizer/`             | Fertilizer recommendation interface |
| `chatbot/`                | AI chatbot                          |
| `weather/`                | Weather functionality               |
| `government_schemes/`     | Government schemes                  |
| `equipment_rental/`       | Equipment management                |
| `marketplace/`            | Marketplace functionality           |
| `soil/`                   | Soil functionality                  |
| `.gitignore`              | Files excluded from Git             |
| `.gitattributes`          | Git LFS configuration               |

---

# 🎯 Project Goal

Smart Sheti combines conventional web application development with AI/ML capabilities to provide farmers with a single platform for:

```text
Crop Management
       +
Disease Detection
       +
Pest Detection
       +
Fertilizer Recommendation
       +
Crop Prediction
       +
Weather
       +
Government Schemes
       +
AI Chatbot
       ↓
Smart Farming Assistance
```

---

# 👨‍💻 Development Notes

When modifying the project:

1. Activate the virtual environment.
2. Pull the latest Git changes.
3. Pull Git LFS files.
4. Install/update dependencies if required.
5. Update Django migrations after model changes.
6. Never commit `.env`.
7. Never commit datasets.
8. Never commit generated training runs.
9. Use Git LFS for large required model files.
10. Test the affected module before pushing.

---
## 📄 Publication

**Research Paper**: AI BASED SMART FARMING SUPPORT PLATFORM 
**DOI:** https://doi.org/10.56726/IRJMETS99199

# 👨‍💻 Author

**Somesh Thombare**

Smart Sheti — AI BASED SMART FARMING SUPPORT PLATFORM


