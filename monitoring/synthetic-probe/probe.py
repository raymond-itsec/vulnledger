"""Synthetic auth-flow probe for the VulnLedger observability stack.

Runs login -> refresh -> logout against the backend on a fixed interval
and exposes the result as Prometheus metrics on /metrics. A liveness
probe catches a 200 on /health; this catches auth regressions that a
liveness probe cannot - a broken JWT signer, a refresh-token rotation
bug, a database that accepts connections but rejects the auth query.

Runs on the app tier so `backend` resolves by local Docker DNS in
allinone, samedc, and crossdc alike.
"""

import logging
import os
import time

import requests
from prometheus_client import Gauge, start_http_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("synthetic-probe")

BASE_URL = os.environ.get("PROBE_TARGET_URL", "http://backend:8000").rstrip("/")
USERNAME = os.environ.get("PROBE_USERNAME", "")
PASSWORD = os.environ.get("PROBE_PASSWORD", "")
INTERVAL = int(os.environ.get("PROBE_INTERVAL", "300"))
METRICS_PORT = int(os.environ.get("PROBE_METRICS_PORT", "8900"))
TIMEOUT = float(os.environ.get("PROBE_HTTP_TIMEOUT", "10"))

up = Gauge(
    "vl_synthetic_auth_up",
    "1 if the last login/refresh/logout cycle fully succeeded, else 0",
)
login_duration = Gauge(
    "vl_synthetic_auth_login_duration_seconds",
    "Duration of the login step in the last cycle",
)
refresh_duration = Gauge(
    "vl_synthetic_auth_refresh_duration_seconds",
    "Duration of the refresh step in the last cycle",
)
logout_duration = Gauge(
    "vl_synthetic_auth_logout_duration_seconds",
    "Duration of the logout step in the last cycle",
)
flow_duration = Gauge(
    "vl_synthetic_auth_flow_duration_seconds",
    "Total duration of the last login/refresh/logout cycle",
)
last_success = Gauge(
    "vl_synthetic_auth_last_success_timestamp_seconds",
    "Unix epoch of the last fully successful cycle",
)


def run_cycle() -> bool:
    """One login -> refresh -> logout cycle. Returns True on full success.

    A requests.Session carries the refresh_token cookie between steps,
    exactly as a browser would.
    """
    session = requests.Session()
    flow_start = time.monotonic()
    try:
        step = time.monotonic()
        resp = session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        login_duration.set(time.monotonic() - step)

        step = time.monotonic()
        resp = session.post(f"{BASE_URL}/api/v1/auth/refresh", timeout=TIMEOUT)
        resp.raise_for_status()
        refresh_duration.set(time.monotonic() - step)

        step = time.monotonic()
        resp = session.post(f"{BASE_URL}/api/v1/auth/logout", timeout=TIMEOUT)
        resp.raise_for_status()
        logout_duration.set(time.monotonic() - step)

        flow_duration.set(time.monotonic() - flow_start)
        last_success.set_to_current_time()
        return True
    except Exception as exc:  # noqa: BLE001 - any failure is a probe failure
        log.warning("probe cycle failed: %s", exc)
        flow_duration.set(time.monotonic() - flow_start)
        return False
    finally:
        session.close()


def main() -> None:
    if not USERNAME or not PASSWORD:
        log.error(
            "PROBE_USERNAME / PROBE_PASSWORD not set - the probe will run "
            "but report down until the synthetic user credentials are provided"
        )
    start_http_server(METRICS_PORT)
    log.info(
        "synthetic-probe serving /metrics on :%d, target %s, interval %ds",
        METRICS_PORT,
        BASE_URL,
        INTERVAL,
    )
    while True:
        ok = run_cycle()
        up.set(1 if ok else 0)
        log.info("cycle complete: up=%d", 1 if ok else 0)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
