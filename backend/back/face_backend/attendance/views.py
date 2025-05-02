import json
import os
import logging
import numpy as np
from PIL import Image
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.utils.timezone import localtime


import face_recognition
from .models import User, Attendance

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# CSRF is disabled only for API testing (if frontend sends CSRF token, you can remove this)
@csrf_exempt
def register_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)

    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        aadhaar = request.POST.get('aadhaar')
        password = request.POST.get('password')
        image_file = request.FILES.get('image')

        if not all([name, email, aadhaar, password, image_file]):
            return JsonResponse({"error": "All fields are required."}, status=400)

        fs = FileSystemStorage()
        filename = fs.save(image_file.name, image_file)
        image_path = fs.path(filename)

        image_np = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image_np)

        if not encodings:
            os.remove(image_path)
            return JsonResponse({'error': 'No face detected.'}, status=400)

        encoding_str = json.dumps(encodings[0].tolist())

        hashed_password = make_password(password)

        user = User.objects.create(
            name=name,
            email=email,
            aadhaar=aadhaar,
            password=hashed_password,
            image=filename,
            face_encoding=encoding_str
        )

        # Delete the uploaded image
        if os.path.exists(image_path):
            os.remove(image_path)

        return JsonResponse({'message': 'User registered successfully', 'user_id': user.id}, status=201)

    except Exception as e:
        logger.error(f'Registration error: {e}')
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)

    try:
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return JsonResponse({'error': 'Email and password required.'}, status=400)

        user = User.objects.filter(email=email).first()

        if user and check_password(password, user.password):
            return JsonResponse({'message': 'Login successful', 'user_id': user.id, 'name': user.name})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except Exception as e:
        logger.error(f'Login error: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def mark_attendance(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)

    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'error': 'Image is required'}, status=400)

    fs = FileSystemStorage()
    filename = fs.save(image_file.name, image_file)
    image_path = fs.path(filename)

    try:
        uploaded_image = face_recognition.load_image_file(image_path)
        uploaded_encodings = face_recognition.face_encodings(uploaded_image)

        if len(uploaded_encodings) == 0:
            os.remove(image_path)
            return JsonResponse({'error': 'No face detected'}, status=400)

        uploaded_encoding = uploaded_encodings[0]

        users = User.objects.all()
        for user in users:
            if not user.face_encoding:
                continue

            try:
                known_encoding = np.array(json.loads(user.face_encoding))
            except:
                continue

            results = face_recognition.compare_faces([known_encoding], uploaded_encoding)
            distance = face_recognition.face_distance([known_encoding], uploaded_encoding)[0]

            if results[0] and distance < 0.5:
                Attendance.objects.create(user=user, timestamp=timezone.now())
                os.remove(image_path)
                return JsonResponse({
                    'message': 'Attendance marked',
                    'user': user.name,
                    'time': localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
                })

        os.remove(image_path)
        return JsonResponse({'error': 'Face not recognized'}, status=404)

    except Exception as e:
        os.remove(image_path)
        return JsonResponse({'error': 'Internal server error', 'details': str(e)}, status=500)
