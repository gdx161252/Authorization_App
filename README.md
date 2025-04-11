=============== Jak Zainstalwoać Aplikacje Autoryzacji ===============

Aplikacja była tworzona na systemie windows z pythonme w wersji 3.10, Django w wersji 5.2.  ! Inne wersje mogą nie działać !


1. Skopiuj repozytorium

  Najpierw sklonuj repozytorium na swój komputer. Otwórz terminal (np. Git Bash) i wpisz:

    git clone https://github.com/gdx161252/Authorization_App.git

2. Utwórz i  Wejdź do katalogu projektu

Po sklonowaniu repozytorium, przejdź do katalogu projektu:

    np. C:\Users\User\PycharmProjects\Authorization_App

3. Zainstaluj wymagane zależności

Projekt wykorzystuje Python i zależności z pliku requirements.txt. Aby zainstalować wszystkie niezbędne biblioteki, wykonaj następujące kroki:

  a) Upewnij się, że masz zainstalowanego Pythona

    python --version

  b) Utwórz wirtualne środowisko (opcjonalnie)

    python -m venv venv

Aktywuj środowisko:

    venv\Scripts\activate

  c) Zainstaluj zależności

Zainstaluj wszystkie wymagane biblioteki z pliku requirements.txt, WAŻNE żeby wersje były takie jak w tym pliku, inaczej niektóre funkcjonalności mogą nie działać !:

    pip install -r requirements.txt

Dodatkowo (na windows) musisz pobrać "dlib-19.22.99-cp310-cp310-win_amd64" z strony

    https://www.cgohlke.com/#dlib Dliba-a

I Pózniej go zainstalować tam gdzie go pobraliśmy:

     pip install ściezka/do/dlib

4.Dodaj swój adres Email oraz mail_password_application z którego będzie wysyłany kod autoryzacji do zmiany hasła

W Pliku views.py w linijkach 175-176 dodaj swój email oraz mail_password_application
![obraz](https://github.com/user-attachments/assets/72949fb8-6f9c-4116-985f-3eaac59683e9)

Mail_password_application możesz znaleźć logując się na swoje konto gmail na:

    https://support.google.com/mail/answer/185833?hl=en

  ![obraz](https://github.com/user-attachments/assets/3d6a729b-4e74-4214-9787-067a14c9a89d)


5. Migracje bazy danych 

       python manage.py migrate

6. Uruchom projekt

Aby uruchomić aplikację, użyj polecenia:

    python manage.py runserver

Po tym, aplikacja powinna być dostępna pod adresem: http://127.0.0.1:8000.

Wejdź na swoją przeglądarkę i wejdź na adres:

    http://127.0.0.1:8000
