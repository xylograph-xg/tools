"""HTTP 基础设施：per-instance 限流锁 + 双预算重试（简化自 findpapers ConnectorBase）。"""
import json
import math
import sqlite3
from email.utils import parsedate_to_datetime
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


class ConnectorError(Exception):
    pass


class DeferredRequest(ConnectorError):
    def __init__(self, retry_at, reason):
        self.retry_at = retry_at
        super().__init__(reason)



class HttpClient:
    def __init__(self, min_interval=0.2, timeout=30, max_retries=3, max_rate_limit_retries=5):
        self.min_interval = min_interval
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_rate_limit_retries = max_rate_limit_retries
        self._lock = threading.Lock()
        self._last_request = 0.0

    def _rate_limit(self):
        with self._lock:
            wait = self.min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def get_json(self, url, params=None, headers=None):
        if params:
            params = {k: v for k, v in params.items() if v not in (None, "")}
            url = f"{url}?{urllib.parse.urlencode(params)}"
        req_headers = {"User-Agent": "literature-explorer/0.1"}
        if headers:
            req_headers.update(headers)

        retries = 0
        while True:
            self._cooldown(url)
            self._rate_limit()
            request = urllib.request.Request(url, headers=req_headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code in (429, 503):
                    delay = self._backoff(e, base=5, attempt=1)
                    retry_at = time.time() + delay
                    self._cooldown(url, retry_at)
                    e.close()
                    raise DeferredRequest(retry_at, f"HTTP {e.code}; provider deferred") from e
                if e.code in (500, 502, 504) and retries < self.max_retries:
                    retries += 1
                    delay = self._backoff(e, base=1, attempt=retries)
                    if delay > 5:
                        retry_at = time.time() + delay
                        self._cooldown(url, retry_at)
                        e.close()
                        raise DeferredRequest(retry_at, f"HTTP {e.code}; provider deferred") from e
                    e.close()
                    time.sleep(delay)
                    continue
                raise ConnectorError(f"HTTP {e.code} for {url}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if retries < self.max_retries:
                    retries += 1
                    time.sleep(self._backoff(None, base=1, attempt=retries))
                    continue
                raise ConnectorError(f"request failed for {url}: {e}") from e

    @staticmethod
    def _backoff(error, base, attempt):
        if error is not None:
            retry_after = getattr(error.headers, "get", lambda *_: None)("Retry-After")
            if retry_after:
                try:
                    value = float(retry_after)
                    if math.isfinite(value) and value >= 0:
                        return value
                except ValueError:
                    try:
                        return max(0, parsedate_to_datetime(retry_after).timestamp() - time.time())
                    except (ValueError, TypeError, OverflowError):
                        pass
        delay = min(base * 2 ** attempt, 60)
        return delay + random.uniform(0, delay * 0.25)

    @staticmethod
    def _cooldown(url, retry_at=None):
        import config
        from pathlib import Path
        path = Path(str(config.DB_PATH) + '.http-cooldowns.sqlite3')
        path.parent.mkdir(parents=True, exist_ok=True)
        host = urllib.parse.urlsplit(url).netloc.lower()
        with sqlite3.connect(path, timeout=5) as db:
            db.execute('CREATE TABLE IF NOT EXISTS cooldowns(host TEXT PRIMARY KEY,retry_at REAL NOT NULL)')
            if retry_at is not None:
                db.execute('INSERT INTO cooldowns VALUES(?,?) ON CONFLICT(host) '
                    'DO UPDATE SET retry_at=max(retry_at,excluded.retry_at)', (host,retry_at))
            else:
                row = db.execute('SELECT retry_at FROM cooldowns WHERE host=?', (host,)).fetchone()
                if row and row[0] > time.time():
                    raise DeferredRequest(row[0], 'provider cooldown active')
