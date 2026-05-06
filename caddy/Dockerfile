FROM caddy:2.11.2-builder-alpine@sha256:113249e07ac54f02da3e395a7150124562af1a3129b0b1498ddbb39f5b3fc430 AS builder

# Pin caddy-ratelimit to a specific commit. Without an explicit tag/commit,
# xcaddy resolves to the latest at build time - a backdoored release would
# silently land on next image rebuild. Update this commit hash deliberately
# after reviewing the diff at https://github.com/mholt/caddy-ratelimit/commits
RUN xcaddy build v2.11.2 \
  --with github.com/mholt/caddy-ratelimit@v0.1.0

FROM caddy:2.11.2-alpine@sha256:834468128c7696cec0ceea6172f7d692daf645ae51983ca76e39da54a97c570d

USER root
RUN apk add --no-cache libcap
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY volume-migrate.sh /usr/local/bin/volume-migrate.sh
RUN chmod 0755 /usr/bin/caddy \
  && chmod 0755 /usr/local/bin/volume-migrate.sh \
  && setcap 'cap_net_bind_service=+ep' /usr/bin/caddy \
  && apk del libcap

USER 10001:10001

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
