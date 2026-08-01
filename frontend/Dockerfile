FROM nginx:alpine

# Copy frontend files
COPY . /usr/share/nginx/html

# Replace the default nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
