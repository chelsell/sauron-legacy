# Cheatsheet

### Start valinor (webserver)

Caddyfile at `/etc/caddy/Caddyfile`:

```
valinor.ucsf.edu {
    root /var/www
    log /var/log/caddy/caddy.log
    proxy / localhost:9000 {
        except /assets/*
        except /var/www/assets/*
    }
    proxy /bots localhost:8000 {
        without /bots
    }
    ratelimit * / 20 10 second
}
```

```bash
ulimit -n 8192
/usr/local/bin/caddy -log stdout -agree=true -conf=/etc/caddy/Caddyfile -root=/var/tmp &!
cd /<<path-to-valinor>>/
sbt run
```
