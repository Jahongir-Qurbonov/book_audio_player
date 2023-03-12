from django.urls import path
from .views import get_book_audio, download_book_audio

urlpatterns = [
    path(
        "<str:book_url_name>/<str:audio_url_name>/", get_book_audio, name="audio-detail"
    ),
    path(
        "<str:book_url_name>/<str:audio_url_name>/d/",
        download_book_audio,
        name="audio-download",
    ),
]
