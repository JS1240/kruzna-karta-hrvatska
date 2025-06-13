# SSL Certificates

Place your production TLS certificate and key files here.

- `fullchain.pem` – certificate chain for your domain
- `privkey.pem` – private key for your domain

These files are mounted into the Nginx container at `/etc/nginx/ssl` when running the production compose configuration.
