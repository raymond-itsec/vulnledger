# WireGuard mesh for VulnLedger multi-host

This directory contains a tiny key-generation helper plus a config
template for the 4-peer (or 5-peer with admin host) WireGuard mesh
that ties multi-host VulnLedger deployments together.

It is **only required for cross-DC mode**. Same-DC operators with a
shared private network can skip WireGuard entirely (or use it as
defense-in-depth without changing anything in this directory).

## Files

| File | What it does |
|---|---|
| `generate-keys.sh` | Generates one private + public key per peer, writes to a local `keys/` directory (gitignored). Run once during initial setup. |
| `wg0.conf.template` | Per-host WireGuard config template. Substitute placeholders (this host's private key, this host's WG IP, peer public keys, peer endpoints) and place at `/etc/wireguard/wg0.conf` on each host. |

## Setup overview

1. Pick a `/24` for the WG overlay. RFC1918 ranges work; `10.99.0.0/24` is a common choice. Don't conflict with your existing networks.
2. Decide the peer-to-IP mapping. Convention: `vl-edge=.1`, `vl-app=.2`, `vl-data=.3`, `vl-monitoring=.4`, admin-host=.5 (if you join the mesh from your laptop).
3. Run `./generate-keys.sh` on a trusted machine (your laptop). This produces `keys/<peer>.priv` and `keys/<peer>.pub` per peer.
4. For each host, copy `wg0.conf.template`, substitute the placeholders for THIS host's identity and the OTHER hosts' peer blocks, install at `/etc/wireguard/wg0.conf` (mode 0600, owner root).
5. Bring up: `systemctl enable --now wg-quick@wg0` on each host.
6. Verify reachability: `ping <peer-wg-ip>` from any host should reach any other.
7. Add `/etc/hosts` entries on all hosts mapping `vl-edge.vuln.lan`, `vl-app.vuln.lan`, etc. to the WG overlay IPs.

## Security notes

- Private keys never leave the machine they were generated on. The helper script writes keys to `keys/` which is in this repo's `.gitignore` — they should never be committed.
- Each host's public NIC firewall must allow UDP 51820 (the WG port) inbound. All other traffic between hosts goes through the WG tunnel.
- Rotate keys when adding or removing peers. There is no PKI; trust is per-key, peer-by-peer.
