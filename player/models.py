import uuid
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.sessions.models import Session

fs = FileSystemStorage(location="audios")


def image_upload_to(instance: "Book", filename):
    return "images/{0}/{1}".format(instance.url_name, filename)


def audio_upload_to(instance: "Audio", filename):
    return "{0}/{1}".format(instance.book.url_name, filename)


class Book(models.Model):
    name = models.CharField(max_length=150)
    url_name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    image = models.ImageField(upload_to=image_upload_to, blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Audio(models.Model):
    book = models.ForeignKey(Book, related_name="audios", on_delete=models.PROTECT)

    name = models.CharField(max_length=150)
    url_name = models.CharField(max_length=150, unique=True)
    audio = models.FileField(upload_to=audio_upload_to, storage=fs)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.book.name}: {self.name}"

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            if not self.name:
                if self.url_name.isdecimal():
                    self.name = f"{self.url_name}-qism"
                else:
                    self.name = self.url_name.capitalize

        return super().save(*args, **kwargs)


class SessionAudio(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)
