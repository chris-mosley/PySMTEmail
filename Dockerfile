FROM python:3.8-alpine


RUN apk update && apk add build-base unixodbc-dev msodbcsql18_18.1.2.1-1_amd64.apk mssql-tools18_18.1.1.1-1_amd64.apk
# RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/msodbcsql18_18.1.2.1-1_amd64.apk && curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/mssql-tools18_18.1.1.1-1_amd64.apk && curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/msodbcsql18_18.1.2.1-1_amd64.sig && curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/mssql-tools18_18.1.1.1-1_amd64.sig && curl https://packages.microsoft.com/keys/microsoft.asc  | gpg --import -gpg --verify msodbcsql18_18.1.2.1-1_amd64.sig msodbcsql18_18.1.2.1-1_amd64.apk && gpg --verify mssql-tools18_18.1.1.1-1_amd64.sig mssql-tools18_18.1.1.1-1_amd64.apk && sudo apk add --allow-untrusted msodbcsql18_18.1.2.1-1_amd64.apk && sudo apk add --allow-untrusted mssql-tools18_18.1.1.1-1_amd64.apk && 

RUN pip3 install requests setuptools pyodbc google-api-python-client google-auth-httplib2 google-auth-oauthlib 

COPY ./*.py /bin/
WORKDIR /bin

CMD ["python", "-u", "./main.py"]