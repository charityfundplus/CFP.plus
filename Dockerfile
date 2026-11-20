# Stage 1: render content/pages/*.md into <ID>/index.html (stdlib only).
# If any content file is invalid this stage fails, the image is not built,
# and the currently running revision keeps serving (safe failure).
FROM python:3.12-alpine AS pages
WORKDIR /src
COPY . /src
RUN python3 tools/build_pages.py

# Stage 2: static site served by nginx (unchanged routing).
FROM nginx:alpine

COPY --from=pages /src /usr/share/nginx/html

RUN printf 'server {\n\
    listen 8080;\n\
    server_name _;\n\
    absolute_redirect off;\n\
    port_in_redirect off;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    charset utf-8;\n\
    location ~ ^/[0-9]+(?:/[0-9]+)*/?$ {\n\
        try_files $uri/index.html $uri /id/index.html;\n\
    }\n\
    location ~* \\.md$ {\n\
        types { }\n\
        default_type text/plain;\n\
    }\n\
    location / {\n\
        try_files $uri/index.html $uri =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
