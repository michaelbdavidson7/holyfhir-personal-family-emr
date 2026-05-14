FROM busybox:stable-musl

# copy all files to the image
COPY . /www/

USER 65534:65534
EXPOSE 8080

CMD ["httpd", "-f", "-p", "8080", "-h", "/www"]
