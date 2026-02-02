# BA Assistant

Business Analyst Assistant - AI-powered tool for requirement documentation.

[![codecov](https://codecov.io/github/itsvetkov1/XtraSkill/graph/badge.svg)](https://codecov.io/github/itsvetkov1/XtraSkill)

## Overview

BA Assistant helps business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## Project Structure

```
BA_assistant/
├── backend/     # FastAPI backend (Python)
└── frontend/    # Flutter web application
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Frontend

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

## Documentation

- [Frontend README](frontend/README.md) - Flutter app setup and testing
- [API Documentation](http://localhost:8000/docs) - OpenAPI/Swagger (when backend running)

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v                           # Run all tests
pytest tests/ --cov=app --cov-report=html  # With coverage
```

### Frontend Tests

```bash
cd frontend
flutter test                    # Run all tests
flutter test --coverage         # With coverage
./coverage_report.sh            # Generate HTML report
```

## License

Proprietary - All rights reserved.
