#!/usr/bin/env bash
set -euo pipefail

TMP_V4=$(mktemp /tmp/roa_dn42_4.XXXXXX)
TMP_V6=$(mktemp /tmp/roa_dn42_6.XXXXXX)
trap 'rm -f "$TMP_V4" "$TMP_V6"' EXIT

if curl -sSLf -o "$TMP_V4" https://dn42.burble.com/roa/dn42_roa_bird2_4.conf && \
   curl -sSLf -o "$TMP_V6" https://dn42.burble.com/roa/dn42_roa_bird2_6.conf; then
    chmod 644 "$TMP_V4" "$TMP_V6"
    mv "$TMP_V4" /etc/bird/roa_dn42.conf
    mv "$TMP_V6" /etc/bird/roa_dn42_v6.conf
    birdc configure > /dev/null
    logger -t dn42-update-roa "DN42 ROA tables updated and BIRD reconfigured successfully."
else
    logger -t dn42-update-roa -p user.err "Failed to update DN42 ROA tables."
    exit 1
fi
