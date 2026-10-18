FROM python:3.12-alpine AS public-builder
WORKDIR /source
COPY . .
RUN python scripts/build_public_site.py --output /public \
    && find /public -type d -exec chmod 0755 {} + \
    && find /public -type f -exec chmod 0644 {} +

FROM nginx:alpine
COPY --from=public-builder /public/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
