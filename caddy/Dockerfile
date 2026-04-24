FROM caddy:2.11.2-builder-alpine@sha256:113249e07ac54f02da3e395a7150124562af1a3129b0b1498ddbb39f5b3fc430 AS builder

RUN xcaddy build v2.11.2 \
  --with github.com/mholt/caddy-ratelimit

FROM caddy:2.11.2-alpine@sha256:834468128c7696cec0ceea6172f7d692daf645ae51983ca76e39da54a97c570d

USER root
RUN apk add --no-cache libcap su-exec
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/bin/caddy \
  && chmod 0755 /usr/local/bin/entrypoint.sh \
  && setcap -r /usr/bin/caddy || true \
  && addgroup -S -g 10001 caddy \
  && adduser -S -D -H -u 10001 -G caddy -s /sbin/nologin caddy \
  && mkdir -p /data /config /var/lib/caddy /tmp \
  && chown -R caddy:caddy /data /config /var/lib/caddy /tmp \
  && apk del libcap

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
