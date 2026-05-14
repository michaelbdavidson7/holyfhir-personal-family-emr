FROM busybox:stable-musl

COPY index.html /www/index.html

USER 65534:65534
EXPOSE 8080

CMD ["httpd", "-f", "-p", "8080", "-h", "/www"]
