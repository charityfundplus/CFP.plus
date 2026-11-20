# Stage 1: render content/pages/*.md into <ID>/index.html (stdlib only).
# If any content file is invalid this stage fails, the image is not built,
# and the currently running revision keeps serving (safe failure).
FROM python:3.12-alpine AS pages
WORKDIR /src
COPY . /src
RUN python3 tools/build_pages.py && rm -rf tools deploy

# Stage 2: static site served by nginx.
FROM nginx:alpine
COPY --from=pages /src /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
