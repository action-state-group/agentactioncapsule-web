FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html 404.html robots.txt sitemap.xml /usr/share/nginx/html/
COPY favicon.ico favicon-32.png apple-touch-icon.png icon-192.png og-image.png /usr/share/nginx/html/
COPY docs/ /usr/share/nginx/html/docs/
RUN chmod -R a+rX /usr/share/nginx/html
EXPOSE 8080
