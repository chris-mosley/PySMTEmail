FROM alpine:latest AS mssql

RUN apk update && apk add curl gpg gnupg 

RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/msodbcsql18_18.1.2.1-1_amd64.apk
# RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/mssql-tools18_18.1.1.1-1_amd64.apk

RUN #(Optional) Verify signature, if 'gpg' is missing install it using 'apk add gnupg':
RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/msodbcsql18_18.1.2.1-1_amd64.sig
# RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/mssql-tools18_18.1.1.1-1_amd64.sig

RUN curl https://packages.microsoft.com/keys/microsoft.asc  | gpg --import -
RUN gpg --verify msodbcsql18_18.1.2.1-1_amd64.sig msodbcsql18_18.1.2.1-1_amd64.apk
# RUN gpg --verify mssql-tools18_18.1.1.1-1_amd64.sig mssql-tools18_18.1.1.1-1_amd64.apk
RUN apk add --allow-untrusted msodbcsql18_18.1.2.1-1_amd64.apk
# RUN apk add --allow-untrusted mssql-tools18_18.1.1.1-1_amd64.apk


FROM python:3.10-alpine AS pyodbc

RUN apk update && apk add build-base unixodbc unixodbc-dev curl gpg gnupg 
RUN pip3 install pyodbc

FROM python:3.10-alpine AS prod

COPY --from=mssql /opt/microsoft /opt/microsoft
COPY --from=mssql /etc/odbcinst.ini /etc/odbcinst.ini
COPY --from=pyodbc /usr/local/lib/python3.10/site-packages/pyodbc* /usr/local/lib/python3.10/site-packages/
# COPY --from=pyodbc /usr/lib/* /usr/lib
COPY --from=pyodbc /usr/lib/libstdc++* /usr/lib
COPY --from=pyodbc /usr/lib/libodbc* /usr/lib
COPY --from=pyodbc /usr/lib/libgcc* /usr/lib
RUN pip3 install requests setuptools google-api-python-client google-auth-httplib2 google-auth-oauthlib


COPY ./*.py /bin/
WORKDIR /bin

CMD ["python", "-u", "./main.py"]