#!/bin/sh
set -eu

TARGETARCH="${TARGETARCH:-amd64}"
SUPERCRONIC_VERSION="${SUPERCRONIC_VERSION:-0.2.45}"
SUPERCRONIC_SHA1_AMD64="${SUPERCRONIC_SHA1_AMD64:-e894b193bea75a5ee644e700c59e30eedc804cf7}"
SUPERCRONIC_SHA1_ARM64="${SUPERCRONIC_SHA1_ARM64:-20ce6dace414a64f0632f4092d6d3745db6085ad}"

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
