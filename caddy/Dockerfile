FROM caddy:2.11.3-builder-alpine@sha256:52575959b1eeee9900869325a953d71e4c521ab9102dd5cce07d429ea8246b85 AS builder

# Pin caddy-ratelimit to a specific commit. Without an explicit tag/commit,
# xcaddy resolves to the latest at build time - a backdoored release would
# silently land on next image rebuild. Update this commit hash deliberately
# after reviewing the diff at https://github.com/mholt/caddy-ratelimit/commits
RUN xcaddy build v2.11.3 \
  --with github.com/mholt/caddy-ratelimit@v0.1.0

FROM caddy:2.11.3-alpine@sha256:86deaf5e3d3408a6ccec08fbb79989783dd26e206ae10bcf78a801dc8c9ab794

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
