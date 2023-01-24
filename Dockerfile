FROM python:3.8-alpine

RUN pip3 install requests google-api-python-client google-auth-httplib2 google-auth-oauthlib

COPY ./*.py /bin/
WORKDIR /bin

CMD ["python", "-u", "./pysmtemail.py"]