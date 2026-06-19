#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests

csv.field_size_limit(sys.maxsize)
OUT = Path("smoody_full_output")
RAW = OUT / "raw"
OUT.mkdir(exist_ok=True)
RAW.mkdir(exist_ok=True)
DB = OUT / "leads.sqlite"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.6"})
SOURCE_PAGE = "https://www.ftc.go.kr/www/selectBizCommOpenList.do?key=255"
DOWNLOAD_BASE = "https://www.ftc.go.kr/www/downloadBizComm.do?atchFileUrl=dataopen&atchFileNm="

REGIONS = [
    ("서울특별시", ["서울특별시"]), ("경기도", ["경기도"]),
    ("부산광역시", ["부산광역시"]), ("대구광역시", ["대구광역시"]),
    ("인천광역시", ["인천광역시"]), ("광주광역시", ["광주광역시"]),
    ("대전광역시", ["대전광역시"]), ("울산광역시", ["울산광역시"]),
    ("세종특별자치시", ["세종특별자치시"]),
    ("충청북도", ["충청북도"]), ("충청남도", ["충청남도"]),
    ("전북특별자치도", ["전북특별자치도", "전라북도"]),
    ("전라남도", ["전라남도"]), ("경상북도", ["경상북도"]),
    ("경상남도", ["경상남도"]),
    ("강원특별자치도", ["강원특별자치도", "강원도"]),
    ("제주특별자치도", ["제주특별자치도"]),
]

EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])([a-z0-9][a-z0-9._%+\-]{0,63}@[a-z0-9][a-z0-9.\-]{1,190}\.[a-z]{2,24})(?![\w.-])")
SMART_RE = re.compile(r"(?i)(?:https?://)?(?:m\.)?(?:sell\.)?(smartstore\.naver\.com|brand\.naver\.com|storefarm\.naver\.com)/([a-z0-9][a-z0-9_\-]{1,79})")
CAFE_RE = re.compile(r"(?i)(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9_\-]{1,63}\.cafe24\.com)(?:[/\s,;|]|$)")
CUSTOM_URL_RE = re.compile(r"(?i)(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?)+(?:/[^\s,;|]*)?)")
SMART_MARKER = re.compile(r"(?i)스마트\s*스토어|스토어팜|smartstore|storefarm")
CAFE_HOST_MARKER = re.compile(r"(?i)보라매로\s*5길\s*15|전문건설회관")

BAD_EMAIL_DOMAINS = {"example.com", "email.com", "domain.com", "sentry.io", "wixpress.com", "naver.com.invalid"}
BAD_EMAIL_PREFIXES = ("noreply", "no-reply", "donotreply", "do-not-reply", "abuse", "postmaster", "webmaster", "privacy", "security")
BAD_CAFE_SUBDOMAINS = {"www", "eclogin", "service", "help", "hosting", "developer", "developers", "img", "image", "images", "api", "admin", "mall", "store"}
EXCLUDED = (
    "담배", "전자담배", "성인용품", "성인오락", "카지노", "도박", "사행", "바카라", "슬롯",
    "약국", "한약국", "병원", "의원", "치과", "보건업", "의료기관", "수의업", "동물병원",
    "금융업", "보험업", "대출", "가상자산", "비트코인", "부동산업", "부동산중개",
    "법무", "세무", "회계", "관세사", "감정평가", "흥신소", "신용조사", "채권추심",
    "유흥주점", "무도장", "콜라텍", "안마시술", "휴게텔", "키스방", "점술", "사주", "골프장 운영",
)
LARGE = ("삼성전자", "LG전자", "엘지전자", "롯데", "신세계", "현대백화점", "아모레퍼시픽", "쿠팡 주식회사", "다이소", "이랜드")


def clean(v: object) -> str:
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def compact(v: str) -> str:
    return re.sub(r"[\s_\-()/·.,]+", "", clean(v)).lower()


def col(columns: list[str], *needles: str) -> str | None:
    pairs = [(c, compact(c)) for c in columns]
    for needle in needles:
        n = compact(needle)
        for original, normalized in pairs:
            if normalized == n or n in normalized:
                return original
    return None


def public_email(raw: str) -> str:
    for value in EMAIL_RE.findall(clean(raw)):
        e = value.lower().strip(" <>[](){}.,;:\"'")
        if "*" in e:
            continue
        local, domain = e.split("@", 1)
        if domain in BAD_EMAIL_DOMAINS or local.startswith(BAD_EMAIL_PREFIXES):
            continue
        if domain.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
            continue
        return e
    return ""


def email_status(raw: str, email: str) -> str:
    if email:
        return "공개 이메일"
    if "*" in clean(raw):
        return "마스킹"
    return "미기재"


def excluded(text: str) -> bool:
    t = clean(text).lower()
    return any(k.lower() in t for k in EXCLUDED + LARGE)


def category(items: str) -> str:
    t = clean(items)
    groups = [
        (("의류", "패션", "신발", "가방", "잡화", "주얼리", "액세서리"), "패션·잡화"),
        (("화장품", "미용", "뷰티", "향수", "헤어", "네일"), "뷰티·화장품"),
        (("식품", "건강", "농산", "수산", "축산", "음료", "커피"), "식품·건강"),
        (("가구", "인테리어", "주방", "생활", "리빙", "수납"), "리빙·홈"),
        (("전자", "컴퓨터", "통신", "가전", "디지털", "사무용품"), "디지털·가전"),
        (("문구", "도서", "완구", "취미", "공예", "오락"), "문구·취미"),
        (("스포츠", "레저", "등산", "골프", "캠핑", "여행", "공연"), "스포츠·레저"),
        (("반려", "애완", "동물"), "반려동물"),
        (("자동차", "차량"), "자동차용품"),
    ]
    for keys, label in groups:
        if any(k in t for k in keys):
            return label
    return "종합몰·기타"


def scenario(cat: str) -> str:
    return {
        "패션·잡화": "상품 추천 AI, 상세페이지·SNS 문구 생성, 사이즈·배송 FAQ 자동응대",
        "뷰티·화장품": "제품 추천·상담 AI, 성분·사용법 FAQ, 리뷰·콘텐츠 자동화",
        "식품·건강": "상품·원산지·배송 FAQ, 재구매 추천, 프로모션 콘텐츠 자동화",
        "리빙·홈": "상품 비교·추천, 재고·배송 문의 자동응대, 상세페이지 생성",
        "디지털·가전": "스펙 비교·호환성 안내, AS·배송 FAQ, 상품 설명 자동화",
        "문구·취미": "용도별 상품 추천, 콘텐츠·상세페이지 생성, 고객문의 자동화",
        "스포츠·레저": "사용 목적별 추천, 규격·배송 FAQ, 캠페인 콘텐츠 생성",
        "반려동물": "반려 조건별 상품 추천, 급여·사용법 FAQ, 재구매 안내",
        "자동차용품": "차종·규격 호환성 안내, 상품 추천, 설치·배송 FAQ",
    }.get(cat, "고객문의 자동응대, 상품 추천, 상세페이지·마케팅 문구 생성")


def description(region: str, platform: str, cat: str) -> str:
    return f"{region} 소재 {platform} 기반 {cat} 온라인 판매 사업자"


def normalize_custom(raw: str) -> str:
    m = CUSTOM_URL_RE.search(clean(raw))
    if not m or "@" in m.group(0):
        return ""
    value = m.group(1).rstrip("/.,;)")
    host, _, path = value.partition("/")
    host = host.lower().removeprefix("www.")
    if host.endswith(("naver.com", "coupang.com", "gmarket.co.kr", "auction.co.kr", "11st.co.kr", "instagram.com", "facebook.com", "youtube.com", "blog.naver.com")):
        return ""
    return "https://" + host + ("/" + path if path else "")


def smart_urls(raw: str) -> list[tuple[str, str, str]]:
    out = []
    for m in SMART_RE.finditer(clean(raw)):
        host, slug = m.group(1).lower(), m.group(2)
        if slug.lower() in {"home", "login", "products", "category", "notice", "seller", "sell"}:
            continue
        platform = "네이버 브랜드스토어" if host.startswith("brand") else "네이버 스마트스토어"
        public_host = "brand.naver.com" if platform == "네이버 브랜드스토어" else "smartstore.naver.com"
        url = f"https://{public_host}/{slug}"
        item = (platform, url, slug)
        if item not in out:
            out.append(item)
    return out


def cafe_urls(raw: str) -> list[tuple[str, str]]:
    out = []
    for m in CAFE_RE.finditer(clean(raw)):
        host = m.group(1).lower().removeprefix("www.")
        sub = host.split(".")[0]
        if sub in BAD_CAFE_SUBDOMAINS:
            continue
        item = (f"https://{host}", sub)
        if item not in out:
            out.append(item)
    return out


def download(region: str, aliases: list[str]) -> tuple[Path | None, str, str]:
    for alias in aliases:
        filename = f"통신판매사업자_ALL_{alias} 전체.csv"
        url = DOWNLOAD_BASE + quote(filename)
        path = RAW / f"{region}.csv"
        try:
            with S.get(url, timeout=(20, 600), stream=True, allow_redirects=True) as r:
                print("DOWNLOAD", region, alias, r.status_code, r.headers.get("content-length"), flush=True)
                if r.status_code != 200:
                    continue
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)
            if path.exists() and path.stat().st_size > 1000:
                return path, alias, url
        except Exception as e:
            print("DOWNLOAD_ERROR", region, alias, repr(e), flush=True)
    return None, "", ""


def init_db() -> sqlite3.Connection:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""CREATE TABLE confirmed(
        website TEXT PRIMARY KEY, platform TEXT, company_name TEXT, brand TEXT,
        public_email TEXT, email_status TEXT, description TEXT, category TEXT,
        items TEXT, region TEXT, legal_type TEXT, report_date TEXT, report_no TEXT,
        business_status TEXT, source_url TEXT, source_file TEXT, confidence TEXT,
        ai_scenario TEXT, contact_priority TEXT, extracted_at TEXT)""")
    con.execute("""CREATE TABLE generic_candidates(
        candidate_key TEXT PRIMARY KEY, company_name TEXT, public_email TEXT,
        category TEXT, items TEXT, region TEXT, legal_type TEXT, report_date TEXT,
        report_no TEXT, search_url TEXT, source_url TEXT, source_file TEXT,
        ai_scenario TEXT, contact_priority TEXT, extracted_at TEXT)""")
    con.execute("""CREATE TABLE cafe_candidates(
        website TEXT PRIMARY KEY, company_name TEXT, brand TEXT, public_email TEXT,
        email_status TEXT, description TEXT, category TEXT, items TEXT, region TEXT,
        legal_type TEXT, report_date TEXT, report_no TEXT, business_status TEXT,
        host_server TEXT, source_url TEXT, source_file TEXT, confidence TEXT,
        ai_scenario TEXT, contact_priority TEXT, extracted_at TEXT)""")
    return con


def upsert_confirmed(con: sqlite3.Connection, values: tuple) -> None:
    con.execute("""INSERT INTO confirmed VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(website) DO UPDATE SET
      company_name=CASE WHEN excluded.report_date>=confirmed.report_date THEN excluded.company_name ELSE confirmed.company_name END,
      public_email=CASE WHEN excluded.public_email<>'' THEN excluded.public_email ELSE confirmed.public_email END,
      email_status=CASE WHEN excluded.public_email<>'' THEN '공개 이메일' ELSE confirmed.email_status END,
      report_date=MAX(confirmed.report_date,excluded.report_date),
      report_no=CASE WHEN excluded.report_date>=confirmed.report_date THEN excluded.report_no ELSE confirmed.report_no END,
      source_file=confirmed.source_file||';'||excluded.source_file""", values)


def process_file(con: sqlite3.Connection, path: Path, region: str, source_url: str) -> Counter:
    stats = Counter()
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        columns = [clean(x).lstrip("\ufeff") for x in (reader.fieldnames or [])]
        reader.fieldnames = columns
        name_c = col(columns, "상호", "업체명", "회사명")
        email_c = col(columns, "전자우편", "이메일", "e-mail")
        domain_c = col(columns, "인터넷도메인", "도메인", "홈페이지")
        status_c = col(columns, "업소상태", "영업상태", "상태")
        item_c = col(columns, "취급품목", "취급상품", "판매품목", "업종")
        legal_c = col(columns, "법인여부", "개인법인구분", "법인구분")
        agency_c = col(columns, "신고기관명", "소재지")
        date_c = col(columns, "신고일자", "등록일자")
        report_c = col(columns, "통신판매번호", "신고번호")
        host_c = col(columns, "호스트서버소재지", "서버소재지")
        if not name_c or not domain_c:
            raise RuntimeError(f"required columns missing: {columns}")
        for row in reader:
            stats["rows"] += 1
            status = clean(row.get(status_c, "")) if status_c else ""
            if "정상" not in status:
                continue
            stats["active"] += 1
            name = clean(row.get(name_c, ""))
            raw_domain = clean(row.get(domain_c, ""))
            items = clean(row.get(item_c, "")) if item_c else ""
            if not name or not raw_domain or raw_domain.lower() == "null":
                continue
            if excluded(name + " " + items):
                stats["excluded"] += 1
                continue
            raw_email = clean(row.get(email_c, "")) if email_c else ""
            email = public_email(raw_email)
            estat = email_status(raw_email, email)
            cat = category(items)
            reg = clean(row.get(agency_c, "")) if agency_c else region
            legal = clean(row.get(legal_c, "")) if legal_c else "확인 필요"
            report_date = re.sub(r"\D", "", clean(row.get(date_c, ""))) if date_c else ""
            report_no = clean(row.get(report_c, "")) if report_c else ""
            host_server = clean(row.get(host_c, "")) if host_c else ""
            extracted = time.strftime("%Y-%m-%d")
            exact = False
            for platform, website, brand in smart_urls(raw_domain):
                exact = True
                priority = "A" if email else "B"
                values = (website, platform, name, brand, email, estat,
                          description(reg, platform, cat), cat, items, reg, legal,
                          report_date, report_no, status, SOURCE_PAGE, path.name,
                          "높음-공개 등록 URL", scenario(cat), priority, extracted)
                upsert_confirmed(con, values); stats["smartstore"] += 1
            for website, brand in cafe_urls(raw_domain):
                exact = True
                priority = "A" if email else "B"
                values = (website, "Cafe24", name, brand, email, estat,
                          description(reg, "Cafe24", cat), cat, items, reg, legal,
                          report_date, report_no, status, SOURCE_PAGE, path.name,
                          "높음-Cafe24 직접 도메인", scenario(cat), priority, extracted)
                upsert_confirmed(con, values); stats["cafe24_direct"] += 1
            if not exact and SMART_MARKER.search(raw_domain) and email:
                key = "|".join((name.lower(), email, reg.lower()))
                query = quote(name + " 스마트스토어")
                search_url = "https://search.naver.com/search.naver?query=" + query
                con.execute("""INSERT OR IGNORE INTO generic_candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (key, name, email, cat, items, reg, legal, report_date, report_no,
                     search_url, SOURCE_PAGE, path.name, scenario(cat), "C", extracted))
                stats["smartstore_generic_email"] += 1
            if not exact and CAFE_HOST_MARKER.search(host_server):
                custom = normalize_custom(raw_domain)
                if custom:
                    brand = custom.split("//", 1)[1].split(".")[0]
                    priority = "B" if email else "C"
                    con.execute("""INSERT INTO cafe_candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(website) DO UPDATE SET
                      public_email=CASE WHEN excluded.public_email<>'' THEN excluded.public_email ELSE cafe_candidates.public_email END,
                      email_status=CASE WHEN excluded.public_email<>'' THEN '공개 이메일' ELSE cafe_candidates.email_status END,
                      report_date=MAX(cafe_candidates.report_date,excluded.report_date)""",
                      (custom, name, brand, email, estat, description(reg, "Cafe24 호스팅 후보", cat),
                       cat, items, reg, legal, report_date, report_no, status, host_server,
                       SOURCE_PAGE, path.name, "중간-Cafe24 호스트 소재지", scenario(cat), priority, extracted))
                    stats["cafe24_host_candidate"] += 1
            if stats["rows"] % 25000 == 0:
                con.commit(); print("PROGRESS", region, dict(stats), flush=True)
    con.commit()
    return stats


def export_table(con: sqlite3.Connection, query: str, path: Path) -> int:
    cur = con.execute(query)
    headers = [d[0] for d in cur.description]
    count = 0
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(headers)
        while True:
            rows = cur.fetchmany(5000)
            if not rows:
                break
            w.writerows(rows); count += len(rows)
    return count


def main() -> int:
    con = init_db()
    logs = []
    for region, aliases in REGIONS:
        path, alias, download_url = download(region, aliases)
        if not path:
            logs.append({"region": region, "status": "download_failed"})
            continue
        try:
            stats = process_file(con, path, region, download_url)
            logs.append({"region": region, "status": "ok", "alias": alias,
                         "bytes": path.stat().st_size, **dict(stats)})
        except Exception as e:
            logs.append({"region": region, "status": "parse_failed", "error": repr(e)})
            print("PARSE_ERROR", region, repr(e), flush=True)
        finally:
            try: path.unlink()
            except Exception: pass

    confirmed_count = export_table(con,
        "SELECT platform,company_name,brand,public_email,email_status,description,website,category,items,region,legal_type,report_date,report_no,business_status,confidence,ai_scenario,contact_priority,source_url,source_file,extracted_at FROM confirmed ORDER BY CASE WHEN public_email<>'' THEN 0 ELSE 1 END, platform, region, company_name",
        OUT / "confirmed_all.csv")
    generic_count = export_table(con,
        "SELECT company_name,public_email,category,items,region,legal_type,report_date,report_no,search_url,ai_scenario,contact_priority,source_url,source_file,extracted_at FROM generic_candidates ORDER BY region,company_name",
        OUT / "smartstore_generic_candidates.csv")
    cafe_candidate_count = export_table(con,
        "SELECT company_name,brand,public_email,email_status,description,website,category,items,region,legal_type,report_date,report_no,business_status,host_server,confidence,ai_scenario,contact_priority,source_url,source_file,extracted_at FROM cafe_candidates ORDER BY CASE WHEN public_email<>'' THEN 0 ELSE 1 END,region,company_name",
        OUT / "cafe24_host_candidates.csv")

    platform_counts = dict(con.execute("SELECT platform,COUNT(*) FROM confirmed GROUP BY platform").fetchall())
    email_counts = dict(con.execute("SELECT platform,SUM(CASE WHEN public_email<>'' THEN 1 ELSE 0 END) FROM confirmed GROUP BY platform").fetchall())
    region_counts = dict(con.execute("SELECT region,COUNT(*) FROM confirmed GROUP BY region ORDER BY COUNT(*) DESC").fetchall())
    stats = {
        "confirmed_total": confirmed_count,
        "confirmed_by_platform": platform_counts,
        "confirmed_with_public_email_by_platform": email_counts,
        "generic_smartstore_candidates_with_email": generic_count,
        "cafe24_host_candidates": cafe_candidate_count,
        "confirmed_by_region": region_counts,
        "source_logs": logs,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": SOURCE_PAGE,
    }
    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), "utf-8")
    with open(OUT / "source_log.csv", "w", encoding="utf-8-sig", newline="") as f:
        keys = sorted({k for x in logs for k in x})
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(logs)
    con.close()
    try: DB.unlink()
    except Exception: pass
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)
    return 0 if confirmed_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
