import os
import cv2
import face_recognition
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, Response, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

known_faces_dir = "known_faces"
attendance_list = []  # List to store attendance records

# Load known faces and their encodings
def load_known_faces(known_faces_dir):
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(known_faces_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            image = face_recognition.load_image_file(os.path.join(known_faces_dir, filename))
            face_locations = face_recognition.face_locations(image)
            if face_locations:  # Check if any face is detected
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                known_face_encodings.append(encoding)
                known_face_names.append(os.path.splitext(filename)[0])
            else:
                print(f"No face detected in {filename}")

    return known_face_encodings, known_face_names

# Check if 12 hours have passed since last attendance
def can_mark_attendance(name):
    if os.path.exists("attendance.csv"):
        attendance_df = pd.read_csv("attendance.csv")
        if not attendance_df.empty:
            # Get the last attendance record for the person
            person_records = attendance_df[attendance_df['Name'] == name]
            if not person_records.empty:
                last_attendance = datetime.strptime(person_records.iloc[-1]['Time'], "%Y-%m-%d %H:%M:%S")
                time_difference = datetime.now() - last_attendance
                if time_difference < timedelta(hours=12):
                    print(f"Cannot mark attendance for {name}. 12 hours haven't passed since last attendance.")
                    return False
    return True

# Mark attendance
def mark_attendance(name):
    if can_mark_attendance(name):
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        attendance_list.append({"Name": name, "Time": dt_string})
        print(f"Attendance marked for: {name} at {dt_string}")  # Debug statement
        
        # Save to CSV immediately after marking attendance
        attendance_df = pd.DataFrame(attendance_list)
        attendance_df.to_csv("attendance.csv", index=False)
        print("Attendance saved to attendance.csv")

# Load known faces
known_face_encodings, known_face_names = load_known_faces(known_faces_dir)

# Video capture generator
def gen_frames():
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Error: Could not open video capture device")
        return
    
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            # Process frame for face recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            
            if face_locations:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                    name = "Unknown"
                    
                    if len(known_face_encodings) > 0:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            mark_attendance(name)
                    
                    # Draw rectangle and name on frame
                    top, right, bottom, left = face_locations[0]
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Add debug print statements
        print(f"Received username: {username}")
        print(f"Received password: {password}")
        
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('home'))
        else:
            error_message = f"Invalid credentials. Username: {username}, Password: {password}"
            print(error_message)  # Debug print
            return render_template('admin_login.html', error=error_message)
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        image_file = request.files['image']
        
        if not name or not image_file:
            return render_template('register.html', message="All fields are required.")
        
        save_path = os.path.join('known_faces', f"{name}.jpg")
        image_file.save(save_path)
        
        # Reload known faces immediately
        global known_face_encodings, known_face_names
        known_face_encodings, known_face_names = load_known_faces(known_faces_dir)
        
        return render_template('register.html', message=f"User '{name}' registered successfully.")
    
    return render_template('register.html')

@app.route('/')
def home():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('index.html')

@app.route('/webcam')
def webcam():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('webcam.html')

@app.route('/video_feed')
def video_feed():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/view_attendance')
def view_attendance():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if os.path.exists("attendance.csv"):
        try:
            attendance_df = pd.read_csv("attendance.csv")
            if attendance_df.empty:
                return "No attendance data found."
            return render_template('attendance.html', attendance=attendance_df.to_dict('records'))
        except pd.errors.EmptyDataError:
            return "The attendance file is empty."
    else:
        return "No attendance data found."

@app.route('/logout')
def logout():
    # Clear the admin session
    session.pop('admin_logged_in', None)
    
    # Delete attendance.csv if it exists
    if os.path.exists("attendance.csv"):
        os.remove("attendance.csv")
        print("Old attendance file removed.")
    
    # Clear in-memory attendance list
    attendance_list.clear()
    print("In-memory attendance list cleared.")
    
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)