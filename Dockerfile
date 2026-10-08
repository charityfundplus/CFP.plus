FROM python:3.12-alpine AS public-builder
WORKDIR /source
COPY . .
RUN python scripts/build_public_site.py --output /public

FROM nginx:alpine
COPY --from=public-builder /public/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
