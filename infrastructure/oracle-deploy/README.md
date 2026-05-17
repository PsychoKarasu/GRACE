# Deploying GRACE on Oracle Cloud Always Free

End-to-end playbook to deploy the GRACE prototype to a free, persistent,
internet-reachable VM on Oracle Cloud Infrastructure. From zero to a live
HTTPS URL the analysts can open: ~40 minutes.

> **Scope of this deployment.** Use it for synthetic / public / non-sensitive
> data only. Real organizational data requires a sanctioned enterprise
> environment with a Data Processing Agreement in place. See
> `backend/data/synthetic/README.md` for the synthetic dataset workflow.

---

## 0. What you'll end up with

```
Internet ─HTTPS─► caddy:443 ─► grace-frontend:8501 ─► grace-backend:8000
                  (Let's Encrypt)    (Streamlit)          (FastAPI)
                                                                │
                                                                ▼
                                                        api.anthropic.com
```

- A single public URL like `https://grace-demo.duckdns.org`
- TLS handled automatically by Caddy (Let's Encrypt)
- Backend and frontend ports NOT exposed to the internet
- Password gate in front of the UI (single shared password)
- Persistent SQLite in a Docker volume on the VM disk
- Cost: **0 EUR/month for the VM forever**; only Anthropic API usage costs

---

## 1. Prerequisites (5 min)

You need:

- A credit card (for Oracle account verification — **no charges** if you
  stay within Always Free limits)
- An SSH key pair on your laptop (`ssh-keygen -t ed25519` if you don't
  have one)
- An `ANTHROPIC_API_KEY` from https://console.anthropic.com
- A demo password you've decided on (something like
  `correct horse battery staple — pick yours`)

---

## 2. Create the Oracle Cloud account (10 min)

1. Go to https://signup.cloud.oracle.com/ and complete sign-up.
   Choose your home region carefully — it's permanent and decides
   data residency. For an EU deployment with GDPR alignment, pick
   **Germany Central (Frankfurt)** or **Netherlands Northwest
   (Amsterdam)**. For Italy proximity, **Italy Northwest (Milan)** is
   available.
2. The verification email and SMS take a couple of minutes.
3. Once in, you land on the OCI Console at `cloud.oracle.com`.

---

## 3. Launch the Always Free VM (5 min)

In the OCI Console:

1. Top-left hamburger menu → **Compute → Instances → Create Instance**.
2. **Name**: `grace-demo`.
3. **Image and shape**:
   - Image: **Canonical Ubuntu 22.04** (Always Free eligible).
   - Shape: click **Change shape → Ampere → VM.Standard.A1.Flex**.
     Set OCPUs = **4**, Memory = **24 GB** (the whole Always Free
     ARM allocation; you can also go smaller, but it costs the same:
     zero). If A1.Flex shows "Out of capacity" in your region, try
     a different availability domain dropdown, or fall back to
     **VM.Standard.E2.1.Micro** (smaller AMD x86, also Always Free).
4. **Networking**: leave the auto-generated VCN selected.
   **Public IPv4 address: Assign**.
5. **SSH keys**: paste your public key (the contents of
   `~/.ssh/id_ed25519.pub`).
6. **Boot volume**: leave default 50 GB.
7. **Show advanced options → Management → User data**:
   paste the contents of `cloud-init.yml` from this directory.
   This installs Docker, opens ports 80/443 at the OS firewall, sets
   up fail2ban, and configures unattended security updates — all on
   first boot, no manual SSH needed.
8. Click **Create**. Provisioning takes ~3 minutes.

When the instance turns green ("Running"), note its **Public IPv4
Address** — you'll use it for SSH and DNS.

---

## 4. Open ports at the VCN level (3 min)

Oracle has TWO firewalls in series: the VCN Security List (cloud
network) AND the VM's iptables (OS). cloud-init handled the OS.
Now open the VCN:

1. In the instance page, click the **Virtual cloud network** link
   under "Primary VNIC".
2. Click the public subnet (usually `Public Subnet-…`).
3. Click the **Security List** named `Default Security List for …`.
4. **Add Ingress Rules**, two of them:

   | Source CIDR | IP Protocol | Destination Port |
   |---|---|---|
   | `0.0.0.0/0` | TCP | `80` |
   | `0.0.0.0/0` | TCP | `443` |

   Leave `Stateless = No`. Save.

(For SSH on 22, the rule is already present by default.)

---

## 5. First SSH + sanity check (2 min)

```bash
ssh ubuntu@<PUBLIC_IP>
```

Verify cloud-init completed:

```bash
ls -la /var/log/grace-cloud-init.done   # exists → bootstrap OK
docker --version                         # Docker installed
docker compose version                   # Compose plugin installed
sudo iptables -L INPUT -n | grep -E '80|443'   # ports open at OS firewall
```

If the marker file is missing, follow live progress with
`sudo tail -f /var/log/cloud-init-output.log` until it says
"GRACE VM bootstrap completed".

---

## 6. Point a DNS name at the VM (5 min)

You need a hostname for Let's Encrypt to issue a TLS certificate.
Cheapest path: free DuckDNS subdomain.

1. Visit https://www.duckdns.org and log in with GitHub or Google.
2. Pick a subdomain, e.g. `grace-demo` → gives you
   `grace-demo.duckdns.org`.
3. Set the **current ip** field to your VM's public IPv4 → **update ip**.
4. Verify resolution from your laptop:
   `dig +short grace-demo.duckdns.org` should print the VM IP.

Alternatives:
- Cloudflare-managed subdomain of a domain you already own — same idea,
  point an A record at the VM IP.
- A free subdomain from no-ip.com or afraid.org if you don't want
  DuckDNS.

---

## 7. Deploy GRACE (5 min)

Back in the SSH session:

```bash
# Clone the repository onto the VM (use your fork or this canonical one)
git clone https://github.com/PsychoKarasu/GRACE.git ~/grace
cd ~/grace
git checkout claude/troubleshoot-grace-app-lr2CQ   # branch with Phase 2 deploy artefacts
cd infrastructure

# Create the production env file from the template
cp .env.example .env
nano .env   # fill in ANTHROPIC_API_KEY, GRACE_DEMO_PASSWORD, GRACE_DOMAIN
```

Set these three at minimum:

```
ANTHROPIC_API_KEY=sk-ant-...
GRACE_DEMO_PASSWORD=<pick a long random string>
GRACE_DOMAIN=grace-demo.duckdns.org
```

Save (`Ctrl+O`, `Enter`, `Ctrl+X`). Then start the stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

First build downloads images and builds Python deps — takes ~3-5 minutes.

When it's up:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
# All three services should show "Up" status

docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f grace-caddy
# Watch for: "certificate obtained successfully" — Let's Encrypt cert issued
```

---

## 8. Verify the public URL (2 min)

From your laptop:

```bash
curl -sI https://grace-demo.duckdns.org   # adapt to your domain
# Expect: HTTP/2 200, with Server: header and HSTS
```

Open `https://grace-demo.duckdns.org` in a browser → you should see the
GRACE password gate. Enter the password from your `.env` and you're in.

Hand the URL and password to the analysts. Done.

---

## 9. Load the synthetic demo dataset (3 min, optional but recommended)

So analysts have something to play with on first visit. Easiest path:
generate the dataset on the VM and upload to the backend over the
loopback binding.

```bash
# On the VM, inside ~/grace
export ANTHROPIC_API_KEY="$(grep ^ANTHROPIC_API_KEY infrastructure/.env | cut -d= -f2-)"

python3 -m venv /tmp/synth-venv
/tmp/synth-venv/bin/pip install --quiet anthropic httpx

/tmp/synth-venv/bin/python tools/synth_assessments.py \
    --framework all --count 3 --coverage random \
    --upload --backend-url http://127.0.0.1:8000 \
    --yes
```

The `--backend-url http://127.0.0.1:8000` works because the base compose
publishes the backend on the loopback interface — reachable from the VM
itself but not from outside. ~12 docs, ~$0.30 of API usage, ~2 minutes.

Alternative: generate on your laptop with the same command pointed at
the local dev backend, then `scp` the resulting `.md` files into the VM
and upload them through the UI.

---

## 10. Day-2 operations

Logs:

```bash
cd ~/grace/infrastructure
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail 100
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs grace-backend
```

Update GRACE (after a new commit on the branch you deployed):

```bash
cd ~/grace
git pull
cd infrastructure
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Backup the SQLite database:

```bash
# Run from VM
docker run --rm \
    -v infrastructure_grace-data:/data:ro \
    -v $(pwd):/backup \
    alpine tar czf /backup/grace-db-$(date +%Y%m%d).tar.gz /data
# Then scp grace-db-*.tar.gz to your laptop
```

Stop everything:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

Restart on VM reboot: handled automatically — both `restart:
unless-stopped` in the compose file and the Docker systemd service
ensure containers come back up after `reboot`.

---

## 11. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `curl https://...` → connection refused or timeout | VCN Security List doesn't allow 443. Check step 4. |
| `curl https://...` → certificate error | Caddy couldn't reach Let's Encrypt — DNS doesn't resolve to the VM IP yet (wait 5 min and retry), or port 80 is closed (Let's Encrypt validates over 80). |
| `docker compose up` fails with "permission denied" on `docker.sock` | You're not in the docker group yet. `sudo usermod -aG docker $USER && exec sg docker -- bash`, or just log out and back in. |
| Streamlit page loads but websocket errors in browser console | Check Caddy logs — websocket forward should work out of the box; if not, verify `Caddyfile` is mounted read-only and not modified. |
| ANTHROPIC_API_KEY rate-limit errors in backend logs | Your demo is hot. Either upgrade your Anthropic plan, switch the engine to `claude-haiku-4-5` in `grc_engine.py`, or rotate the GRACE_DEMO_PASSWORD to throttle access. |
| Disk filling up | `docker system prune -af --volumes` (warning: also drops the grace-data volume if not in use — usually it IS in use by the running stack, so safe). |

---

## 12. Security checklist before sharing the URL

- [ ] `GRACE_DEMO_PASSWORD` is a long, unique random string (not a dictionary word)
- [ ] `.env` is not committed (verify with `git status` — should not appear)
- [ ] Caddy logs show a successful Let's Encrypt cert issuance
- [ ] `nmap -p 22,80,443,8000,8501 <PUBLIC_IP>` from outside shows ONLY 22, 80, 443 open
- [ ] You are only uploading SYNTHETIC / PUBLIC documents (no real
      organizational data on this infra — see top of this README)
- [ ] You've told the analysts that this is a prototype on personal
      infrastructure, not a production system

---

## 13. Cost reality check

| Item | Monthly cost |
|---|---|
| Oracle Cloud VM (ARM A1.Flex 4 OCPU / 24 GB, Always Free) | €0.00 |
| Egress bandwidth (10 TB/month free on Always Free) | €0.00 |
| Block storage (50 GB out of 200 GB free) | €0.00 |
| DuckDNS subdomain | €0.00 |
| Let's Encrypt TLS certificate | €0.00 |
| **Anthropic API usage** (variable) | ~€1–10 depending on demo activity |
| **Total** | **~€1–10/mo, entirely on Anthropic API** |

If Anthropic usage worries you, see `tools/README.md` for cost
optimization (switch to Haiku 4.5 + prompt caching).
