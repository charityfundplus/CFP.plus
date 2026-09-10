FROM nginx:alpine

COPY . /usr/share/nginx/html

RUN printf 'server {\n\
    listen 8080;\n\
    server_name _;\n\
    absolute_redirect off;\n\
    port_in_redirect off;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location ~ ^/[0-9]+(?:/[0-9]+)*/?$ {\n\
        try_files $uri/index.html $uri /id/index.html;\n\
    }\n\
    location / {\n\
        try_files $uri/index.html $uri =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
