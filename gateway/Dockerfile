FROM nginx:alpine

# Remove the default Nginx config (it would conflict with ours)
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom routing config
COPY nginx.conf /etc/nginx/conf.d/

EXPOSE 80
