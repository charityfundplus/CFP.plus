FROM nginx:alpine

COPY . /usr/share/nginx/html

RUN printf 'server {\n\
    listen 8080;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location ~ ^/[0-9]+/?$ {\n\
        try_files $uri $uri/ $uri/index.html /id/index.html;\n\
    }\n\
    location / {\n\
        try_files $uri $uri/ $uri/index.html =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
