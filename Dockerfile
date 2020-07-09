FROM python:3.7-alpine
RUN apk update \
&& apk upgrade \
&& apk add --no-cache bash openssh-client
WORKDIR /usr/src/app
RUN adduser -D -g '' user
USER user
COPY src .
RUN mkdir -pv ~/.config/ltodog
CMD ["python3", "-u", "./ltodog.py"]
