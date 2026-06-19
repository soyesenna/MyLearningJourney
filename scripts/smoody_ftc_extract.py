#!/usr/bin/env python3
"""Extract public SmartStore/Cafe24 prospects from FTC regional CSV files.

Only public business contact email is retained. Phone numbers, representative
names and registration numbers are intentionally omitted.
"""
from __future__ import annotations

import concurrent.futures
import csv
import io
import json
import os
import re
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

OUT = Path("ftc_prospect_output")
OUT.mkdir(exist_ok=True)
RAW = OUT / "raw"
RAW.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.6"})

CITIES = [
    "서울특별시", "경기도", "부산광역시", "인천광역시", "대구광역시",
    "대전광역시", "광주광역시", "울산광역시", "충청북도", "충청남도",
    "경상북도", "경상남도", "전라남도", "전북특별자치도",
    "강원특별자치도", "제주특별자치도", "세종특별자치시",
]

EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])([a-z0-9][a-z0-9._%+\-]{0,63}@[a-z0-9][a-z0-9.\-]{1,190}\.[a-z]{2,24})(?![\w.-])")
URL_RE = re.compile(r"(?i)(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9._-]*(?:\.[a-z0-9][a-z0-9._-]*)+)(/[^\s,;|]*)?")
SMART_RE = re.compile(r"(?i)(?:https?://)?(?:www\.)?(smartstore\.naver\.com|brand\.naver\.com|storefarm\.naver\.com)/([a-z0-9_\-]+)")

BAD_EMAIL_DOMAINS = {"example.com", "email.com", "domain.com", "naver.com.invalid", "sentry.io", "wixpress.com"}
BAD_PREFIXES = ("noreply", "no-reply", "donotreply", "do-not-reply", "abuse", "postmaster", "webmaster", "privacy", "security")
EXCLUDED = (
    "담배", "전자담배", "성인", "카지노", "도박", "슬롯", "바카라", "총포", "무기",
    "병원", "의원", "치과", "약국", "의료", "보험", "대출", "가상자산", "비트코인",
    "부동산", "법무", "세무", "회계", "흥신소", "점술", "사주", "안마", "유흥",
)
LARGE = (
    "삼성전자", "엘지전자", "LG전자", "롯데", "신세계", "현대백화점", "아모레퍼시픽",
    "쿠팡", "다이소", "이랜드", "CJ제일제당", "네이버", "카카오",
)
CAFE24_SIGNATURES = (
    "cafe24", "cafe24.com", "cafe24api", "ec_hosting_api", "cafe24img.com",
    "/ind-script/", "hosting by cafe24", "호스팅제공자 : 카페24", "호스팅제공자: 카페24",
)


def clean(v: object) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def compact(v: str) -> str:
    return re.sub(r"[\s_\-()/·.,]+", "", clean(v)).lower()


def find_col(columns: list[str], *needles: str) -> str | None:
    normalized = [(c, compact(c)) for c in columns]
    for n in needles:
        nn = compact(n)
        for c, cc in normalized:
            if cc == nn or nn in cc:
                return c
    return None


def valid_email(v: str) -> str:
    if not v or "*" in v:
        return ""
    for e in EMAIL_RE.findall(v):
        e = e.lower().strip(" <>[](){}.,;:\"'")
        local, dom = e.split("@", 1)
        if dom in BAD_EMAIL_DOMAINS or local.startswith(BAD_PREFIXES):
            continue
        if dom.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
            continue
        return e
    return ""


def excluded(text: str) -> bool:
    t = clean(text).lower()
    return any(x.lower() in t for x in EXCLUDED + LARGE)


def download_url(city: str) -> str:
    filename = f"통신판매사업자_ALL_{city} 전체.csv"
    return "https://www.ftc.go.kr/www/downloadBizComm.do?atchFileUrl=dataopen&atchFileNm=" + quote(filename)


def download_city(city: str) -> Path | None:
    path = RAW / f"{city}.csv"
    if path.exists() and path.stat().st_size > 1000:
        return path
    url = download_url(city)
    try:
        with S.get(url, timeout=(20, 300), stream=True, allow_redirects=True) as r:
            print("DOWNLOAD", city, r.status_code, r.headers.get("content-type"), r.headers.get("content-disposition"), flush=True)
            if r.status_code != 200:
                return None
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
        if path.stat().st_size < 1000:
            return None
        return path
    except Exception as e:
        print("DOWNLOAD_ERROR", city, repr(e), flush=True)
        return None


def detect_encoding(path: Path) -> str:
    raw = path.read_bytes()[:200000]
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            pass
    return "cp949"


def normalize_smartstore(raw: str) -> tuple[str, str] | None:
    m = SMART_RE.search(raw or "")
    if not m:
        return None
    host, slug = m.group(1).lower(), m.group(2).strip("/_-")
    if not slug:
        return None
    platform = "네이버 브랜드스토어" if host.startswith("brand.") else "네이버 스마트스토어"
    return platform, f"https://{host}/{slug}"


def normalize_domain(raw: str) -> str:
    raw = clean(raw)
    m = URL_RE.search(raw)
    if not m:
        return ""
    host = m.group(1).lower().removeprefix("www.").strip(" .")
    path = clean(m.group(2) or "").rstrip("/")
    if not host or host.endswith(("naver.com", "daum.net", "google.com")):
        return ""
    return f"https://{host}{path if path.startswith('/') else ''}"


def category_from(value: str) -> str:
    t = clean(value)
    if not t:
        return "온라인 쇼핑몰"
    for keys, label in [
        (("의류", "패션", "신발", "가방", "잡화", "주얼리", "액세서리"), "패션·잡화"),
        (("화장품", "미용", "뷰티", "향수", "헤어"), "뷰티·화장품"),
        (("식품", "건강", "농산", "수산", "축산", "음료", "커피"), "식품·건강"),
        (("가구", "인테리어", "주방", "생활", "리빙"), "리빙·홈"),
        (("전자", "컴퓨터", "통신", "가전", "디지털"), "디지털·가전"),
        (("문구", "도서", "완구", "취미", "공예"), "문구·취미"),
        (("스포츠", "레저", "등산", "골프", "캠핑"), "스포츠·레저"),
        (("반려", "애완", "동물"), "반려동물"),
    ]:
        if any(k in t for k in keys):
            return label
    return t[:80]


def parse_city(path: Path, city: str) -> tuple[list[dict], list[dict], dict]:
    enc = detect_encoding(path)
    smart: list[dict] = []
    direct_cafe: list[dict] = []
    customs: list[dict] = []
    stats = Counter()
    with open(path, "r", encoding=enc, errors="replace", newline="") as f:
        sample = f.read(50000)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        columns = [clean(c).lstrip("\ufeff") for c in (reader.fieldnames or [])]
        if not columns:
            return [], [], {"city": city, "error": "no header"}
        # Remap fieldnames stripped of BOM/space.
        reader.fieldnames = columns
        name_c = find_col(columns, "상호", "업체명", "회사명")
        email_c = find_col(columns, "전자우편", "이메일", "e-mail")
        domain_c = find_col(columns, "인터넷도메인", "도메인", "홈페이지")
        status_c = find_col(columns, "업소상태", "영업상태", "상태")
        item_c = find_col(columns, "취급품목", "취급상품", "판매품목", "업종")
        method_c = find_col(columns, "판매방식")
        legal_c = find_col(columns, "법인여부", "개인법인구분", "법인구분")
        agency_c = find_col(columns, "신고기관명", "소재지", "주소")
        report_c = find_col(columns, "통신판매번호", "신고번호")
        print("HEADER", city, columns, flush=True)
        if not name_c or not domain_c:
            return [], [], {"city": city, "error": "required columns missing", "columns": columns}
        for row in reader:
            stats["rows"] += 1
            name = clean(row.get(name_c, ""))
            raw_domain = clean(row.get(domain_c, ""))
            if not name or not raw_domain:
                continue
            status = clean(row.get(status_c, "")) if status_c else ""
            if status and not any(x in status for x in ("정상", "영업", "통신판매")):
                stats["inactive"] += 1
                continue
            items = clean(row.get(item_c, "")) if item_c else ""
            if excluded(name + " " + items):
                stats["excluded"] += 1
                continue
            email = valid_email(clean(row.get(email_c, ""))) if email_c else ""
            base = {
                "company_name": name,
                "brand": "",
                "email": email,
                "category": category_from(items),
                "items": items,
                "region": clean(row.get(agency_c, "")) if agency_c else city,
                "legal_type": clean(row.get(legal_c, "")) if legal_c else "확인 필요",
                "business_status": status or "정상 영업 여부 확인 필요",
                "report_no": clean(row.get(report_c, "")) if report_c else "",
                "source_file": path.name,
                "source_url": "https://www.ftc.go.kr/www/selectBizCommOpenList.do?key=255",
                "email_source_url": "https://www.ftc.go.kr/www/selectBizCommOpenList.do?key=255" if email else "",
            }
            sm = normalize_smartstore(raw_domain)
            if sm:
                platform, website = sm
                p = dict(base, platform=platform, website=website, brand=website.rstrip("/").split("/")[-1], evidence="공정거래위원회 공개 통신판매사업자 자료")
                smart.append(p); stats["smart"] += 1
                continue
            url = normalize_domain(raw_domain)
            if not url:
                continue
            host = urlparse(url).netloc.lower().removeprefix("www.")
            p = dict(base, platform="Cafe24 확인 후보", website=url, brand=host.split(".")[0], evidence="공정거래위원회 공개 통신판매사업자 자료")
            if host.endswith("cafe24.com") or "cafe24.com" in raw_domain.lower():
                p["platform"] = "Cafe24"
                direct_cafe.append(p); stats["cafe24_direct"] += 1
            elif email and len(customs) < 12000:
                customs.append(p)
    return smart, direct_cafe, {"city": city, "encoding": enc, "columns": columns, **stats, "custom_candidates": customs}


def detect_cafe24(p: dict) -> dict | None:
    url = p["website"]
    candidates = [url]
    if not url.endswith("/"):
        candidates.append(url + "/")
    html = ""
    final = url
    for u in candidates:
        try:
            r = S.get(u, timeout=(4, 9), allow_redirects=True, headers={"User-Agent": UA})
            if r.status_code == 200 and r.text:
                html = r.text[:800000]
                final = r.url
                break
        except Exception:
            pass
    low = html.lower()
    if not html or not any(sig.lower() in low for sig in CAFE24_SIGNATURES):
        return None
    p = dict(p)
    p["platform"] = "Cafe24"
    p["website"] = final.split("?")[0].rstrip("/")
    p["evidence"] += "; 공식 웹사이트 Cafe24 기술 서명 확인"
    return p


def dedupe(rows: list[dict]) -> list[dict]:
    out: dict[str, dict] = {}
    for p in rows:
        key = p.get("website", "").lower().rstrip("/")
        if not key:
            continue
        old = out.get(key)
        if old is None or (not old.get("email") and p.get("email")):
            out[key] = p
    return list(out.values())


def main() -> int:
    all_smart: list[dict] = []
    all_cafe: list[dict] = []
    custom_candidates: list[dict] = []
    summaries: list[dict] = []
    target_smart = int(os.environ.get("TARGET_SMART", "1800"))
    target_cafe = int(os.environ.get("TARGET_CAFE", "500"))
    for city in CITIES:
        path = download_city(city)
        if not path:
            summaries.append({"city": city, "error": "download failed"})
            continue
        smart, direct_cafe, st = parse_city(path, city)
        customs = st.pop("custom_candidates", [])
        all_smart.extend(smart)
        all_cafe.extend(direct_cafe)
        if len(custom_candidates) < 12000:
            custom_candidates.extend(customs[: 12000 - len(custom_candidates)])
        summaries.append(st)
        all_smart = dedupe(all_smart)
        all_cafe = dedupe(all_cafe)
        print("COUNTS", city, len(all_smart), len(all_cafe), len(custom_candidates), flush=True)
        if len(all_smart) >= target_smart and len(all_cafe) >= target_cafe:
            break

    # Verify custom-domain Cafe24 candidates in parallel, prioritising public email.
    custom_candidates = dedupe(custom_candidates)
    custom_candidates.sort(key=lambda x: (0 if x.get("email") else 1, x.get("company_name", "")))
    with concurrent.futures.ThreadPoolExecutor(max_workers=48) as ex:
        futures = {ex.submit(detect_cafe24, p): p for p in custom_candidates[:8000]}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                p = fut.result()
                if p:
                    all_cafe.append(p)
            except Exception:
                pass
            if i % 250 == 0:
                all_cafe = dedupe(all_cafe)
                print("CAFE_VERIFY", i, len(all_cafe), flush=True)
            if len(dedupe(all_cafe)) >= target_cafe:
                for pending in futures:
                    pending.cancel()
                break

    all_smart = dedupe(all_smart)
    all_cafe = dedupe(all_cafe)
    # rank public-email and individual businesses first
    def rank(p: dict):
        individual = "개인" in clean(p.get("legal_type")) and "법인" not in clean(p.get("legal_type"))
        return (0 if p.get("email") else 1, 0 if individual else 1, p.get("company_name", ""))
    all_smart.sort(key=rank)
    all_cafe.sort(key=rank)
    rows = all_smart + all_cafe

    fields = [
        "platform", "company_name", "brand", "email", "category", "items", "website",
        "region", "legal_type", "business_status", "report_no", "source_file", "source_url",
        "email_source_url", "evidence",
    ]
    with open(OUT / "prospects.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows([{k: p.get(k, "") for k in fields} for p in rows])
    with open(OUT / "prospects.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    stats = {
        "total": len(rows),
        "smartstore": len(all_smart),
        "cafe24": len(all_cafe),
        "with_email": sum(bool(p.get("email")) for p in rows),
        "smartstore_with_email": sum(bool(p.get("email")) for p in all_smart),
        "cafe24_with_email": sum(bool(p.get("email")) for p in all_cafe),
        "regional_summaries": summaries,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(OUT / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)
    return 0 if len(rows) >= 900 else 2


if __name__ == "__main__":
    raise SystemExit(main())
