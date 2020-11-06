# VERSION 0.0.1
# AUTHOR: Rikkki
# DESCRIPTION: study project for fast api
# BUILD: docker build --rm -t rikkki/crawlBase
# SOURCE: https://github.com/rikiisworking/TPQueryOrganizer

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
LABEL maintainer="Rikkki_"
COPY requirements.txt . 
RUN pip install -r requirements.txt
WORKDIR /home/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]