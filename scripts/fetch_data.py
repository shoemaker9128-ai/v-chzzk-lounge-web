#!/usr/bin/env python3
"""치지직 라이브 목록을 수집해 버추얼 스트리머만 골라 data/lives.json으로 저장한다.

치지직 공개 API는 브라우저 교차 출처 요청(CORS)을 막기 때문에,
정적 홈페이지가 직접 호출할 수 없다. 대신 이 스크립트를 서버(GitHub Actions)에서
주기적으로 실행해 JSON 파일로 만들어 두고, 홈페이지는 그 파일만 읽는다.
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.chzzk.naver.com/service/v1"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
PAGE_SIZE = 50
MAX_PAGES = 8  # 최대 400개 라이브까지 훑는다
VIRTUAL_TAGS = ("버튜버", "버츄얼")
OUT = Path(__file__).resolve().parent.parent / "data" / "lives.json"
PREV = Path(__file__).resolve().parent.parent / "data" / "prev.json"
KST = timezone(timedelta(hours=9))


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def fetch_lives():
    lives = []
    cursor = ""
    for _ in range(MAX_PAGES):
        url = f"{API}/lives?size={PAGE_SIZE}{cursor}"
        content = get(url).get("content") or {}
        data = content.get("data") or []
        lives.extend(data)
        nxt = (content.get("page") or {}).get("next")
        if not nxt or not data:
            break
        cursor = (
            f"&concurrentUserCount={nxt['concurrentUserCount']}"
            f"&liveId={nxt['liveId']}"
        )
        time.sleep(0.3)
    return lives


def is_virtual(live):
    tags = live.get("tags") or []
    return any(
        any(keyword in str(tag) for keyword in VIRTUAL_TAGS) for tag in tags
    )


def follower_count(channel_id, cache):
    if channel_id in cache:
        return cache[channel_id]
    count = None
    try:
        content = get(f"{API}/channels/{channel_id}").get("content") or {}
        count = content.get("followerCount")
    except Exception:
        count = None
    cache[channel_id] = count
    time.sleep(0.1)
    return count


def load_prev():
    try:
        data = json.loads(PREV.read_text(encoding="utf-8"))
        return data.get("savedAt"), {
            str(k): v for k, v in (data.get("viewers") or {}).items()
        }
    except Exception:
        return None, {}


def main():
    lives = fetch_lives()
    virtual = [live for live in lives if is_virtual(live)]
    prev_at, prev_viewers = load_prev()
    cache = {}
    out = []
    for live in virtual:
        channel = live.get("channel") or {}
        channel_id = channel.get("channelId")
        thumb = live.get("liveImageUrl") or live.get("defaultThumbnailImageUrl")
        if thumb:
            thumb = thumb.replace("{type}", "720")
        viewers = live.get("concurrentUserCount") or 0
        trend = None
        before = prev_viewers.get(str(live.get("liveId")))
        if before:
            delta = viewers - before
            trend = {"delta": delta, "pct": round(delta / before * 100)}
        out.append(
            {
                "liveId": live.get("liveId"),
                "title": live.get("liveTitle"),
                "thumbnail": thumb,
                "viewers": viewers,
                "trend": trend,
                "openDate": live.get("openDate"),
                "adult": bool(live.get("adult")),
                "tags": live.get("tags") or [],
                "category": live.get("liveCategoryValue") or "",
                "channel": {
                    "id": channel_id,
                    "name": channel.get("channelName"),
                    "image": channel.get("channelImageUrl"),
                    "verified": bool(channel.get("verifiedMark")),
                    "followers": follower_count(channel_id, cache),
                },
            }
        )
    out.sort(key=lambda x: x["viewers"], reverse=True)
    now = datetime.now(KST)
    payload = {
        "updatedAt": now.isoformat(timespec="seconds"),
        "prevAt": prev_at,
        "count": len(out),
        "lives": out,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    PREV.write_text(
        json.dumps(
            {
                "savedAt": now.isoformat(timespec="seconds"),
                "viewers": {str(l["liveId"]): l["viewers"] for l in out},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"scanned={len(lives)} virtual={len(out)} -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
