# WireGuard mesh for VulnLedger multi-host

Automated mesh setup. From a freshly cloned repo to a working WG mesh
across 4 hosts is 3 commands plus a peer-list edit.

This is **only required for cross-DC mode**. Same-DC operators with a
shared private network can skip WireGuard entirely (or use it as
defense-in-depth without changing anything in this directory).

## TL;DR

```
cp deploy/wireguard/peers.example.txt deploy/wireguard/peers.txt
$EDITOR deploy/wireguard/peers.txt   # set names, WG IPs, public endpoints
make wg-bootstrap                    # generate keys + render per-host configs
make wg-install                      # scp configs to each peer + enable wg-quick
```

For the cold-bootstrap case (peer has no SSH yet), skip `wg-install` and
inject the rendered `out/<peer>.conf` into each host's cloud-init at
provisioning time.

## What's in this directory

| File | Purpose |
|---|---|
| `peers.example.txt` | Sample peer list. Copy to `peers.txt` (gitignored) and edit. |
| `generate-keys.sh` | Per-peer keypair generation. One-time. |
| `render-configs.sh` | Reads `peers.txt` + `keys/`, writes `out/<peer>.conf`. Idempotent. |
| `install-configs.sh` | Optional: scps each `out/<peer>.conf` to its host and enables `wg-quick@wg0`. Requires SSH already reachable. |

## Workflow detail

### 1. Edit `peers.txt`

Pick a `/24` for the WG overlay (RFC1918 ranges; `10.99.0.0/24` is a
common default). Decide the peer-to-IP mapping. Decide each peer's
public endpoint (the host:port on the peer's PUBLIC NIC where WG
handshakes arrive).

### 2. `make wg-bootstrap`

Runs `generate-keys.sh` (creates `keys/<peer>.priv` and `keys/<peer>.pub`
per peer, mode 0600 / 0644) followed by `render-configs.sh` (writes
`out/<peer>.conf` per peer with everything filled in). Both directories
are gitignored.

### 3. `make wg-install`

Reads `peers.txt` again, scps each `out/<peer>.conf` to that peer's
public endpoint host, installs at `/etc/wireguard/wg0.conf`, and runs
`systemctl enable --now wg-quick@wg0`. Requires SSH to each peer
already configured (the install step assumes you're past the
chicken-and-egg of "I need WG to SSH but I need SSH to install WG").

For cold-bootstrap (no SSH yet), inject the conf via cloud-init:

```yaml
# In each host's cloud-init userdata:
write_files:
  - path: /etc/wireguard/wg0.conf
    content: |
      <paste contents of deploy/wireguard/out/vl-edge.conf>
    permissions: '0600'
    owner: root:root
runcmd:
  - systemctl enable --now wg-quick@wg0
```

Or use OVF properties + base64 if your provisioner supports them
(see the optional `vulnledger-lab-esxi` companion repo).

## Adding or removing peers

1. Edit `peers.txt`.
2. Re-run `make wg-bootstrap`. The keys script skips peers that already
   have keys; the render script always rewrites configs.
3. Re-run `make wg-install` (or push the regenerated configs via your
   own provisioning path).

Removed peers do NOT have their keys deleted from `keys/` — that's a
manual step. `rm keys/<peer>.priv keys/<peer>.pub` if you want them
gone permanently.

## Security notes

- **Private keys never leave the machine they were generated on**, except
  via `install-configs.sh` (scp into the right peer). That's the
  intended path.
- **`peers.txt`, `keys/`, and `out/` are all gitignored.** Confirm with
  `git status` before any commit.
- **Each host's public NIC firewall must allow UDP 51820** (or whatever
  `WG_PORT` you set) inbound. All other inter-host traffic rides the
  WG tunnel.
- **Rotate keys** when adding or removing peers if you want to fully
  invalidate an old peer's access. There's no PKI; trust is per-key.

## Make targets reference

| Target | What it does |
|---|---|
| `make wg-keys` | Step 1 of bootstrap: generate keypairs |
| `make wg-render` | Step 2 of bootstrap: render per-host configs |
| `make wg-bootstrap` | wg-keys + wg-render in sequence |
| `make wg-install` | scp configs to each peer + enable wg-quick |
| `make wg-status` | Run `sudo wg show` on each host (manual hint for now) |
