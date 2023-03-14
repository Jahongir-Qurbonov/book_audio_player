import os
from django.http import Http404, HttpRequest, FileResponse, HttpResponse


def process_response(request: HttpRequest, response: FileResponse):
    if response.status_code != 200 or not hasattr(response, "file_to_stream"):
        return response
    http_range = request.META.get("HTTP_RANGE")
    if not (
        http_range and http_range.startswith("bytes=") and http_range.count("-") == 1
    ):
        return response
    if_range = request.META.get("HTTP_IF_RANGE")
    if (
        if_range
        and if_range != response.get("Last-Modified")
        and if_range != response.get("ETag")
    ):
        return response
    f = response.file_to_stream
    statobj = os.fstat(f.fileno())
    start, end = http_range.split("=")[1].split("-")
    if not start:  # requesting the last N bytes
        start = max(0, statobj.st_size - int(end))
        end = ""
    start, end = int(start or 0), int(end or statobj.st_size - 1)
    assert 0 <= start < statobj.st_size, (start, statobj.st_size)
    end = min(end, statobj.st_size - 1)
    f.seek(start)
    # old_read = f.read
    # f.read = lambda n: old_read(min(n, end + 1 - f.tell()))
    response.status_code = 206
    response["Content-Length"] = end + 1 - start
    response["Content-Range"] = "bytes %d-%d/%d" % (start, end, statobj.st_size)
    return response


def send_file_header(server_type):
    header = "X-Sendfile" if server_type == "apache" else "X-Accel-Redirect"
    return header


def range_file(request, file_path):
    if not os.path.exists(file_path):
        raise Http404("File not found")

    # Chunk size
    CHUNK_SIZE = 1024 * 1024 * 2  # 2 MB chunk size

    # Open file for reading
    file_size = os.path.getsize(file_path)
    file = open(file_path, "rb")

    # Set response headers
    response = HttpResponse(content_type="audio/mpeg")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="{os.path.basename(file_path)}"'
    response["Accept-Ranges"] = "bytes"

    # Set content length for the full file
    response["Content-Length"] = str(file_size)

    # Range header handling
    range_header = request.META.get("HTTP_RANGE")
    if range_header:
        # Parse range header
        parts = range_header.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1

        # Calculate content range and content length for the partial content
        content_range = f"bytes {start}-{end}/{file_size}"
        content_length = end - start + 1

        # Set response headers for partial content
        response["Content-Range"] = content_range
        response["Content-Length"] = str(content_length)
        response.status_code = 206

        # Move file pointer to start of the requested range
        file.seek(start)

        # Read the requested range and send it in chunks
        while start <= end:
            chunk_size = min(CHUNK_SIZE, end - start + 1)
            data = file.read(chunk_size)
            response.write(data)
            start += chunk_size
        file.close()

        return response

    # If range header is not present, send the full file
    response.write(file.read())
    file.close()
    return response
