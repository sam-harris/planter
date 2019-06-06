# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
FROM python:3-alpine

# If you prefer miniconda:
#FROM continuumio/miniconda3

LABEL Name=codebase Version=0.0.1

WORKDIR /app

RUN apk update
RUN apk add gcc musl-dev python3-dev libffi-dev openssl-dev make jpeg-dev zlib-dev freetype-dev
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f

COPY ./requirements.txt ./requirements.txt

# Using pip:
RUN python3 -m pip install -r requirements.txt
RUN python3 -c "import imageio; imageio.plugins.freeimage.download()"
CMD ["python3"]
