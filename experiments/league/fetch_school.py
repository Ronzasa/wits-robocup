"""Save a public HTTP GET from the school soccer site with provenance."""
import argparse
import datetime
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


BASE = "https://lamp.ms.wits.ac.za/soccer/"
DESTINATION = Path(__file__).resolve().parent / "school"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Relative URL or public URL on lamp.ms.wits.ac.za")
    parser.add_argument("--name", required=True, help="Evidence filename inside school/")
    parser.add_argument("--timeout", type=int, default=30, help="Public server read timeout, up to 180 seconds")
    args = parser.parse_args()
    url = urllib.parse.urljoin(BASE, args.url)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "lamp.ms.wits.ac.za":
        parser.error("Only HTTPS GETs to lamp.ms.wits.ac.za are allowed")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.name):
        parser.error("Evidence filename must not contain a path")
    if not 1 <= args.timeout <= 180:
        parser.error("--timeout must be between 1 and 180 seconds")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    path = DESTINATION / args.name
    provenance = path.with_name(path.name + ".meta.json")
    if path.exists() or provenance.exists():
        raise FileExistsError("Existing evidence; use a fresh --name")
    request = urllib.request.Request(url, headers={"User-Agent": "SoccerLeagueAudit/1.0"})
    with urllib.request.urlopen(request, timeout=args.timeout) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != "https" or final.hostname != "lamp.ms.wits.ac.za":
            raise ValueError("Unexpected redirect outside the school host")
        data = response.read(20 * 1024 * 1024 + 1)
        if len(data) > 20 * 1024 * 1024:
            raise ValueError("Public response exceeds 20 MiB evidence limit")
        metadata = {"url": url, "final_url": response.url, "status": response.status,
                    "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "content_type": response.headers.get("Content-Type"),
                    "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified"),
                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    with path.open("xb") as stream:
        stream.write(data)
    with provenance.open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2)
    print(json.dumps({**metadata, "file": str(path)}))


if __name__ == "__main__":
    main()
