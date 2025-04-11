import smtplib
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import SecurityQuestionSet, Photo, AuthenticatorProfile
import cv2
from django.contrib.auth.decorators import login_required
import face_recognition
import numpy as np
from django.core.files.base import ContentFile
import os
import pyotp
import random

@login_required
def home(request):
    questions = None
    if request.user.is_authenticated:
        try:
            questions = request.user.securityquestionset
        except SecurityQuestionSet.DoesNotExist:
            questions = None  # jeszcze nie ma rekordu

    photo = Photo.objects.filter(user=request.user).first() #Sprawdzanie czy żytkownik ma zdjecie

    profile, created = AuthenticatorProfile.objects.get_or_create(user=request.user)

    return render(request, 'home.html', {'questions': questions, 'photo': photo, 'profile': profile })
@login_required
def questions(request):
    if request.method == 'POST':
        q1 = request.POST.get('question1')
        q2 = request.POST.get('question2')
        q3 = request.POST.get('question3')

        sqs, created = SecurityQuestionSet.objects.get_or_create(user=request.user)
        sqs.question_1 = q1
        sqs.question_2 = q2
        sqs.question_3 = q3
        sqs.save()

        messages.success(request, "Pytania zapisane poprwanie")
        return render(request, 'questions.html', {'redirect_after': True}) #przekierowanie po wypełnieniu formularza
    return render(request, 'questions.html')

@login_required
def behavioral(request):
    username = request.user.username.lower()
    filename = f"{username}.jpg"

    # Zrób zdjęcie
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    if ret:
        cv2.imwrite(filename, frame)
        print("✅ ZDJĘCIE ZROBIONE POMYŚLNIE")
    else:
        print("❌ Nie udało się uchwycić obrazu z kamery ❌")

    video_capture.release()
    cv2.destroyAllWindows()

    # Odczytaj dane pliku jako bajty
    with open(filename, 'rb') as f:
        file_data = f.read()

    # Pobierz lub stwórz rekord w bazie danych
    photo, created = Photo.objects.get_or_create(user=request.user)

    # Usuń stare zdjęcie, jeśli było
    if photo.image:
        photo.image.delete(save=False)

    # Zapisz nowe zdjęcie do ImageField z nazwą użytkownika
    photo.image.save(f"{username}.jpg", ContentFile(file_data), save=True)

    # Usuń lokalnie zapisany plik tymczasowy
    if os.path.exists(filename):
        os.remove(filename)

    return render(request, 'behavioral.html', {'photo': photo})



def setup_authenticator(request):
    profile, created = AuthenticatorProfile.objects.get_or_create(user=request.user)

    if not profile.otp_secret:
        profile.generate_otp_secret()

    if request.method == "POST":
        code = request.POST.get("code")
        totp = pyotp.TOTP(profile.otp_secret)
        if totp.verify(code):
            profile.authenticator_enabled = True
            profile.save()
            return redirect('home')
        else:
            return render(request, 'register_login.html', {
                'error': "❌ Kod nieprawidłowy",
                'qr_uri': profile.get_totp_uri(),
                'profile': profile

            })

    return render(request, 'setup_authenticator.html', {
        'qr_uri': profile.get_totp_uri(),
        'profile': profile

    })

def authenticator_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        code = request.POST.get('code')

        try:
            user = User.objects.get(username=username)
            profile = AuthenticatorProfile.objects.get(user=user)
        except (User.DoesNotExist, AuthenticatorProfile.DoesNotExist):
            return render(request, 'authenticator_login.html', {
                'error': 'Użytkownik nie istnieje lub nie ma aktywnego Authenticatora.'
            })

        if not profile.authenticator_enabled:
            return render(request, 'authenticator_login.html', {
                'error': 'Użytkownik nie ma aktywowanego logowania przez Authenticator.'
            })

        totp = pyotp.TOTP(profile.otp_secret)
        if totp.verify(code):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'authenticator_login.html', {
                'error': '❌ Niepoprawny kod jednorazowy.'
            })

    return render(request, 'authenticator_login.html')

@login_required
def change_pas(request):
    if request.method == 'POST':

        new_login = request.POST.get('New_login')
        new_password = request.POST.get('New_password')

        if new_login:
            request.user.username = new_login

        if new_password:
            request.user.set_password(new_password)

        request.user.save()

        messages.info(request, 'Zostałeś wylogowany, musisz się zalogować ponownie.')
        return redirect('login')

    return render(request, 'change_pas.html')


def forget(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'Podany email nie istnieje')
            return redirect('forget')

        request.session['user_email'] = email
        EMAIL_ADRESS = ("jakis@Mail.com") # Tutaj wpisać mail z którego będze wysyłany kod
        EMAIL_PASSWORD = ("gmail_app_password") # Tutaj wpisać kod aplikacji z maila. Czyli gmail app password

        code_veryfication = random.randint(100000, 999999)
        title = "Twój kod weryfikacyjny"
        message = f"Twój kod weryfikacyjny do aplikacji python to: {code_veryfication}"

        message = f"Subject: {title}\nContent-Type: text/plain; charset=utf-8\n\n{message}".encode("utf-8")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADRESS, email, message)

        # Przechowywanie kodu w sesji
        request.session['code_veryfication'] = code_veryfication

        messages.error(request, 'Kod został wysłany')

        return redirect('forget_2')

    return render(request, 'forget_pass.html')


def forget_pass_step_2(request):
    page = 'login'

    if request.method == 'POST':
        code = request.POST.get('mail_code')
        security_answer = request.POST.get('security_answer')

        # Odczytujemy kod weryfikacyjny z sesji
        code_veryfication = str(request.session.get('code_veryfication'))
        user_email = request.session.get('user_email')
        selected_question = request.POST.get('selected_question')


        if code_veryfication is not None and user_email:
            if code == code_veryfication :
                try:
                    user = User.objects.get(email=user_email)  # Szukamy użytkownika po e-mailu
                except User.DoesNotExist:
                    messages.error(request, 'Nie znaleziono użytkownika.')
                    return redirect('forget')
                # Zapisujemy flagę weryfikacji w sesji, że użytkownik jest zweryfikowany
                request.session['verified'] = True
                messages.success(request, 'Poprawne dane weryfikacyjne')
                return redirect('forget_3')  # Przekierowanie do formularza zmiany danych

            else:
                    messages.error(request, 'Kod niepoprawny !')

        else:
            messages.error(request, 'Brak kodu weryfikacyjnego lub e-maila w sesji.')

    return render(request, 'forget_pass_step_2.html', {'page': page})


def forget_pass_step_3(request):
    if not request.session.get('verified'):
        return redirect('forget')

    user_email = request.session.get('user_email')

    if not user_email:
        return redirect('forget')

    try:
        user = User.objects.get(email=user_email)  # Znajdujemy użytkownika po e-mailu
    except User.DoesNotExist:
        messages.error(request, 'Nie znaleziono użytkownika.')
        return redirect('forget')

    if request.method == 'POST':

        new_login = request.POST.get('new_login')
        new_password = request.POST.get('new_pass')
        security_answer = request.POST.get('security_answer')
        selected_question = request.POST.get('selected_question')
        sec_questions = SecurityQuestionSet.objects.get(user=user)

        print(selected_question)
        print(sec_questions.question_1)


        if new_login:
            user.username = new_login

        if new_password:
            user.set_password(new_password)

        if (
                selected_question == 'JAK NAZYWA SIĘ TWÓJ ZWIERZAK ?' and security_answer == sec_questions.question_1) or (
                selected_question == 'W JAKIM MIEŚCIE SIĘ URODZIŁEŚ ?' and security_answer == sec_questions.question_2) or (
                selected_question == 'JAKI JEST TWÓJ ULUBIONY FILM ?' and security_answer == sec_questions.question_3):
            user.save()

        else:
            messages.error(request, 'Niepoprawna odpowiedz na pytanie bezpeiczenstwa.')
            return redirect('forget')

        messages.success(request, 'Twoje dane zostały zaktualizowane!')
        return redirect('login')

    return render(request, 'forget_pass_step_3.html')

def register_login(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username) # porównywanie czy to co wpisal uzytkownik jest zgodne z baza danych
        except:
            messages.error(request, 'Użytkownik nie istnieje.')
            return render(request, 'register_login.html', {'page': page})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '❌ Nazwa użytkownika bądż hasło nieprawidłowe ❌')

    context = {'page': page}
    return render(request, 'register_login.html', context)


def register_login_face_id(request):
    page = 'login'

    if request.method == "POST":
        username = request.POST.get('username')

        # Sprawdź, czy użytkownik istnieje
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, '❌ Nie znaleziono użytkownika o takiej nazwie ❌')
            return redirect('login')

        # Spróbuj pobrać zdjęcie wzorcowe
        try:
            photo = Photo.objects.get(user=user)
            image_path = photo.image.path
        except Photo.DoesNotExist:
            messages.error(request, f"❌ Brak zdjęcia wzorcowego dla użytkownika '{username}' ❌")
            return redirect('login')

        # Wczytaj obraz z dysku
        bgr_image = cv2.imread(image_path)

        if bgr_image is None:
            messages.error(request, f"❌ Nie udało się otworzyć zdjęcia: {image_path}")
            return redirect('login')

        # Konwersja do RGB i poprawny format danych
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        rgb_image = np.ascontiguousarray(rgb_image, dtype=np.uint8)

        # 🔧 przerysuj w pamięci
        rgb_image = cv2.imdecode(cv2.imencode('.jpg', rgb_image)[1], cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB)  # jeszcze raz na RGB

        # Wykryj twarz
        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            messages.error(request, "❌ Nie wykryto twarzy na zdjęciu wzorcowym ❌")
            return redirect('login')

        known_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]

        # === Uruchom kamerę i porównaj twarz
        video_capture = cv2.VideoCapture(0)
        is_authenticated = False

        while True:
            ret, frame = video_capture.read()
            if not ret:
                continue

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding in face_encodings:
                match = face_recognition.compare_faces([known_encoding], face_encoding)[0]
                if match:
                    login(request, user)
                    is_authenticated = True
                    break
                else:
                    messages.error(request, '❌ Twarz nierozpoznana - dostęp zabroniony ❌')

            if is_authenticated:
                break

            # Podgląd kamery (można wyłączyć)
            cv2.imshow('Face ID - naciśnij Q, aby zakończyć', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

        return redirect('home' if is_authenticated else 'login')

    return render(request, 'register_login.html', {'page': page})





def register_logout(request):
    logout(request)
    return redirect('login')

def register_register(request):
    if request.method == "POST":
        username = request.POST.get('username').lower()
        email = request.POST.get('email').lower()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Hasła się nie zgadzają')
            return render(request, 'register_login.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Taki użytkownik już istnieje')
            return render(request, 'register_login.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ten email jest już zajęty')
            return render(request, 'register_login.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect('home')

    return render(request, 'register_login.html')