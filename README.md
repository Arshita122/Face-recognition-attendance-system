A Flask-based web application that automates attendance tracking using facial recognition technology.

Features
✅ Real-time face detection using OpenCV
✅ Attendance logging with timestamp
✅ 12-hour cooldown to prevent duplicate entries
✅ Admin dashboard for user management
✅ Responsive web interface with dark theme

Technologies Used
Backend: Python, Flask

Face Recognition: OpenCV, face_recognition

Frontend: HTML5, CSS3

Database: CSV (for attendance records)

Installation
Clone the repository:

bash
git clone https://github.com/yourusername/face-recognition-attendance.git
cd face-recognition-attendance
Install dependencies:

bash
pip install -r requirements.txt
Run the application:

bash
python app.py
Usage
Access the admin panel at http://localhost:5000

Login with credentials:

Username: admin

Password: admin123

Register users by uploading their photos

Use the webcam interface to mark attendance

File Structure
project/
├── app.py                # Main application
├── templates/            # HTML templates
│   ├── index.html        # Dashboard
│   ├── admin_login.html  # Login page
│   ├── register.html     # User registration
│   ├── webcam.html       # Webcam interface
│   └── attendance.html   # Attendance records
├── static/
│   └── styles.css        # Stylesheet
├── known_faces/          # Stores registered user images
└── attendance.csv        # Attendance records
