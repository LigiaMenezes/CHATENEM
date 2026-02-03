"""
Django settings for ChatENEM project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv



# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-key-only"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "chatenem.onrender.com",  # quando fizer deploy
    "localhost",
    "127.0.0.1",
]


# Database (SQLite para desenvolvimento)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================
# SUPABASE CONFIG
# ============================

try:
    SUPABASE_URL = os.environ["SUPABASE_URL"]
    SUPABASE_KEY = os.environ["SUPABASE_KEY"]
except KeyError as e:
    raise RuntimeError(f"Missing required Supabase environment variable: {e}")


# ============================
# LLM / EMBEDDINGS
# ============================

EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "intfloat/multilingual-e5-large"
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# ============================
# APPLICATIONS
# ============================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",

    # Local
    "collector",

    'corsheaders',
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "ChatENEM.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ChatENEM.wsgi.application"


# ============================
# PASSWORD VALIDATION
# ============================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ============================
# INTERNATIONALIZATION
# ============================

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True
USE_TZ = True


# ============================
# STATIC FILES
# ============================

STATIC_URL = "static/"


# ============================
# DEFAULT FIELD
# ============================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'OPTIONS',
]
