from django.http import HttpRequest, HttpResponseNotFound
from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.views.decorators.http import require_GET
from .models import Audio, SessionAudio
from ranged_fileresponse import RangedFileResponse


@require_GET
def get_book_audio(request: HttpRequest, book_url_name, audio_url_name):
    """Get player page"""
    response = render(request, "index.html")

    if request.session.session_key is None:
        request.session.save()
    session = Session.objects.get(session_key=request.session.session_key)
    session_audio, created = SessionAudio.objects.get_or_create(session=session)
    if not created:
        session_audio.delete()
        session_audio = SessionAudio.objects.create(session=session)

    try:
        audio = Audio.objects.get(book__url_name=book_url_name, url_name=audio_url_name)
    except:
        return HttpResponseNotFound("Audio not exist")

    context = {
        "book_name": audio.book.name,
        "audio_name": audio.name,
        # "audio_url": f"/{audio.book.url_name}/{audio.url_name}/d/",
    }
    if audio.book.image:
        context["book_pic"] = audio.book.image.url
    response = render(request, "index.html", context)
    response.set_cookie("session_audio", session_audio.uuid)
    response.set_cookie("audio_url", f"/{audio.book.url_name}/{audio.url_name}/d/")

    return response


@require_GET
def download_book_audio(request: HttpRequest, book_url_name, audio_url_name):
    _session_key = request.session.session_key
    _session_audio_uuid = request.GET.get("q", None)
    if None in (_session_key, _session_audio_uuid):
        return HttpResponseNotFound("File not exist")

    session = Session.objects.get(session_key=_session_key)

    try:
        session_audio = SessionAudio.objects.get(
            session=session, uuid=_session_audio_uuid
        )
    except:
        return HttpResponseNotFound("File not exist")
    # session_audio.delete()

    try:
        audio = Audio.objects.get(
            book__url_name=book_url_name, url_name=audio_url_name
        ).audio
    except:
        return HttpResponseNotFound("File not exist")

    response = RangedFileResponse(request, audio.open("rb"), content_type="audio/mpeg")
    response["Content-Disposition"] = 'attachment; filename="%s"' % audio.name
    return response
