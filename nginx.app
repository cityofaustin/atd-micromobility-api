server {
    listen 80;

    listen 443 ssl;

    location / {
        proxy_pass http://172.18.0.22:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias  /app/static/;
    }
    
}
