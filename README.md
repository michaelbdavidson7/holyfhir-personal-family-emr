HolyFHIR – Personal Family EMR

HolyFHIR is a local-first personal electronic medical record (EMR) designed for individuals and families.
It provides a simple, private way to manage health data while supporting FHIR (Fast Healthcare Interoperability Resources) for import and export.

✨ Features
👨‍👩‍👧‍👦 Family-focused patient management
Manage multiple patient profiles (yourself, children, relatives)
🏥 Clinical records
Medications
Allergies
Conditions
Immunizations
Observations (labs, vitals)
Encounters
📄 Document storage
Upload and manage clinical documents (PDFs, reports, scans)
🔄 FHIR support (in progress)
Import FHIR Bundles and resources
Export patient data as FHIR-compliant JSON
Snapshot storage of raw FHIR data
🖥️ Local-first architecture
Runs entirely on your machine
Uses SQLite (no external database required)
No cloud dependency
🔐 Privacy-first design
Your data stays on your device
No tracking, no external services
🧱 Tech Stack
Backend: Django
Database: SQLite (planned: SQLCipher encryption)
Admin UI: Django Admin + Jazzmin
FHIR Layer: Custom mapping + resource snapshots
Desktop (planned): Tauri or Wails wrapper
🚀 Getting Started
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/holyfhir-personal-family-emr.git
cd holyfhir-personal-family-emr
2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
3. Install dependencies
pip install -r requirements.txt
4. Run migrations
python manage.py migrate
5. Create admin user
python manage.py createsuperuser
6. Start the server
python manage.py runserver
7. Open the app

Go to:

http://127.0.0.1:8000/admin
🗂️ Project Structure
backend/
  apps/
    patients/      # Patient profiles
    clinical/      # Conditions, meds, allergies, etc.
    documents/     # File uploads
    fhir/          # Import/export + snapshots
  config/          # Django settings
  templates/       # Admin overrides (dashboard)
🔄 FHIR Roadmap

Import FHIR Bundle (Patient, Medication, Allergy, Condition)

Export patient as FHIR Bundle

Mapping layer (internal models ↔ FHIR resources)

Validation and error reporting

SMART on FHIR (future)

🔐 Security Roadmap

SQLCipher database encryption

OS keychain integration

Encrypted file storage

Secure export handling

🧭 Vision

HolyFHIR aims to become a simple, private, interoperable personal health record system:

Easy enough for individuals and families
Structured enough for real medical use
Compatible with healthcare standards (FHIR)
Fully under user control
⚠️ Disclaimer

This project is for personal use and experimentation.
It is not a certified medical system and should not be relied upon as a sole source of medical truth.

📌 Status

🚧 Early development (Phase 1 complete – core data + admin UI)

📄 License

TBD