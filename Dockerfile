FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html cpb.html ip.html playground.html 404.html robots.txt sitemap.xml llms.txt /usr/share/nginx/html/
COPY favicon.ico favicon-32.png apple-touch-icon.png icon-192.png og-image.png /usr/share/nginx/html/
COPY docs/ /usr/share/nginx/html/docs/
COPY talks/ /usr/share/nginx/html/talks/
COPY extensions/ /usr/share/nginx/html/extensions/
COPY profiles/ /usr/share/nginx/html/profiles/
# Topic explainers, the build-your-own-evidence-layer pages, and the map over both (#51, #53, #54, #56, #58)
COPY explain/ /usr/share/nginx/html/explain/
COPY build/ /usr/share/nginx/html/build/
COPY map/ /usr/share/nginx/html/map/
RUN chmod -R a+rX /usr/share/nginx/html
EXPOSE 8080
