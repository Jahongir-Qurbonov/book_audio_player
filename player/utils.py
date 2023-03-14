import re
import os
import time
from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse

RANGE_RE = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)

def file_iterator(file_path, chunk_size=8192, offset=0, length=None):
    with open(file_path, "rb") as f:
        f.seek(offset, os.SEEK_SET)
        remaining = length
        while True:
            bytes_length = (
                chunk_size
                if remaining is None 
                else min(remaining, chunk_size)
            )
            data = f.read(bytes_length)
            if not data:
                break
            if remaining:
                remaining -= len(data)
            yield data

def stream_audio(request, audio):
    path = audio.audio.path
    content_type = "audio/mp3"

    range_header = request.META.get("HTTP_RANGE", "").strip()
    range_match = RANGE_RE.match(range_header)
    size = os.path.getsize(path)

    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = (
            first_byte + 1024 * 1024 / 2
        )  # The max volume of the response body is 8M per piece
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        response = StreamingHttpResponse(
            file_iterator(path, offset=first_byte, length=length),
            status=206,
            content_type=content_type,
        )
        response["Content-Range"] = f"bytes {first_byte}-{last_byte}/{size}"

    else:
        response = StreamingHttpResponse(
            FileWrapper(open(path, "rb")), content_type=content_type
        )
    response["Accept-Ranges"] = "bytes"

    # response['X-Accel-Redirect'] = f"/{audio.book.url_name}/{audio.url_name}/d/"
    # response['X-Accel-Buffering'] = 'no'
    response['Content-Length'] = length
    response['Content-Dispostion'] = "attachment; filename=" + audio.name
    return response