FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html robots.txt sitemap.xml /usr/share/nginx/html/
COPY docs/ /usr/share/nginx/html/docs/
# 404 fallback (copy the landing if no dedicated 404 page is provided)
RUN cp /usr/share/nginx/html/index.html /usr/share/nginx/html/404.html \
 && chmod -R a+rX /usr/share/nginx/html
EXPOSE 8080
