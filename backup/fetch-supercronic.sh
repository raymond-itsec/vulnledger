#!/bin/sh
set -eu

TARGETARCH="${TARGETARCH:-amd64}"
SUPERCRONIC_VERSION="${SUPERCRONIC_VERSION:-0.2.44}"
SUPERCRONIC_SHA1_AMD64="${SUPERCRONIC_SHA1_AMD64:-6eb0a8e1e6673675dc67668c1a9b6409f79c37bc}"
SUPERCRONIC_SHA1_ARM64="${SUPERCRONIC_SHA1_ARM64:-6c6cba4cde1dd4a1dd1e7fb23498cde1b57c226c}"

case "$TARGETARCH" in
  amd64) arch="amd64"; expected_sha1="$SUPERCRONIC_SHA1_AMD64" ;;
  arm64) arch="arm64"; expected_sha1="$SUPERCRONIC_SHA1_ARM64" ;;
  *)
    echo "Unsupported TARGETARCH: $TARGETARCH" >&2
    exit 1
    ;;
esac

cache_path="/opt/vendor/supercronic-linux-${arch}"
install_path="/usr/local/bin/supercronic"
url="https://github.com/aptible/supercronic/releases/download/v${SUPERCRONIC_VERSION}/supercronic-linux-${arch}"

if [ -f "$cache_path" ]; then
  cp "$cache_path" "$install_path"
else
  wget -q -O "$install_path" "$url"
fi

echo "${expected_sha1}  ${install_path}" | sha1sum -c -
chmod 0755 "$install_path"
