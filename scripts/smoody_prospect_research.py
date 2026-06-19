#!/usr/bin/env python3
"""Public-web prospect research for Smoody AI.

Sources:
1) BuiltWith public Cafe24 technology/category pages.
2) Korea Fair Trade Commission public mail-order business CSV pages, filtered
   for Naver SmartStore/BrandStore domains.
3) Public storefront homepages for title/description/business email enrichment.

The script intentionally omits telephone numbers and does not infer or invent
email addresses. Masked or unavailable emails remain blank.
"""

from __future__ import annotations

import concurrent.futures
import csv
import json
import os
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

OUT = Path(os.environ.get("OUTPUT_DIR", "research_output"))
OUT.mkdir(parents=True, exist_ok=True)
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7"})

EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])([a-z0-9][a-z0-9._%+\-]{0,63}@[a-z0-9][a-z0-9.\-]{1,190}\.[a-z]{2,24})(?![\w.-])")
DOMAIN_RE = re.compile(
    r"(?i)(?<![@\w-])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:co\.kr|or\.kr|go\.kr|ne\.kr|re\.kr|pe\.kr|kr|com|net|org|shop|store|io|life|world|global|co|me|biz|info|company|market|design|studio|today|care|beauty|fashion|online))(?![\w-])"
)

BLOCKED_EMAIL_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "google.com", "facebook.com",
    "instagram.com", "naver.com.invalid", "domain.com", "email.com",
}
BLOCKED_EMAIL_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply", "abuse", "postmaster",
    "webmaster", "privacy", "security", "support@builtwith",
}
BLOCKED_HOSTS = {
    "builtwith.com", "trends.builtwith.com", "pro.builtwith.com", "google.com",
    "vimeo.com", "facebook.com", "instagram.com", "youtube.com", "twitter.com",
    "x.com", "linkedin.com", "pinterest.com", "cloudflare.com", "w3.org",
    "schema.org", "jquery.com", "naver.com", "pstatic.net",
}
EXCLUDED_KEYWORDS = {
    "전자담배", "담배", "성인용", "성인", "카지노", "도박", "슬롯", "바카라",
    "약국", "한약", "병원", "의원", "치과", "의료", "비트코인", "가상자산",
    "부동산", "보험", "대출", "법무", "세무", "회계", "수의", "흥신소",
    "점술", "사주", "안마", "유흥", "콜라텍",
}
LARGE_BRAND_KEYWORDS = {
    "삼성전자", "삼성물산", "엘지전자", "lg전자", "현대백화점", "롯데", "신세계",
    "아모레퍼시픽", "cj제일제당", "네이버", "카카오", "쿠팡", "다이소", "이랜드",
}

CATEGORY_LABELS = {
    "watches": "시계·액세서리",
    "vitamins": "건강·영양 제품",
    "shoes": "신발",
    "skin-care": "스킨케어·뷰티",
    "skincare": "스킨케어·뷰티",
    "photography": "사진·촬영용품",
    "luggage": "여행가방·여행용품",
    "dinnerware": "식기·테이블웨어",
    "activewear": "스포츠·액티브웨어",
    "lingerie": "이너웨어",
    "instruments": "악기·음향용품",
    "nail-care": "네일·뷰티",
    "nailcare": "네일·뷰티",
    "tennis": "테니스·스포츠용품",
    "home-decor": "홈데코·인테리어",
    "computers": "컴퓨터·디지털",
    "salons": "헤어·살롱용품",
    "furniture": "가구·리빙",
    "sewing": "봉제·공예용품",
    "golf": "골프용품",
    "jewellery": "주얼리·액세서리",
    "jewelry": "주얼리·액세서리",
    "groceries-and-food": "식품·그로서리",
    "food-and-groceries": "식품·그로서리",
    "fragrance": "향수·향 제품",
    "cycling": "자전거·사이클용품",
    "appliances": "생활가전",
    "coats-and-jackets": "패션·아우터",
    "underwear": "이너웨어",
    "apparel": "패션·의류",
    "nutrition": "식품·영양 제품",
    "books": "도서·문구",
    "eyewear": "안경·아이웨어",
    "fashion": "패션·잡화",
    "makeup": "메이크업·뷰티",
    "hair-care": "헤어케어·뷰티",
    "haircare": "헤어케어·뷰티",
    "womens-clothing": "여성의류",
    "coffee": "커피·음료",
    "tableware": "주방·테이블웨어",
    "swimwear": "수영복·레저웨어",
    "party-supplies": "파티·행사용품",
    "bags": "가방·잡화",
    "phones": "휴대폰·모바일 액세서리",
    "fitness": "피트니스·운동용품",
    "kitchenware": "주방용품",
    "general": "온라인 쇼핑몰",
}

# Fallback categories in case the main trend page changes or hides links.
CATEGORY_SLUGS = list(CATEGORY_LABELS.keys())

FTC_CITIES = [
    "서울특별시", "경기도", "인천광역시", "부산광역시", "대구광역시",
    "대전광역시", "광주광역시", "울산광역시", "세종특별자치시",
    "충청북도", "충청남도", "전북특별자치도", "전라남도",
    "경상북도", "경상남도", "강원특별자치도", "제주특별자치도",
]


@dataclass
class Prospect:
    platform: str
    company_name: str
    brand: str
    email: str
    description: str
    website: str
    category: str
    region: str
    legal_type: str
    business_status: str
    source_url: str
    email_source_url: str
    evidence: str


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_domain(value: str) -> str:
    value = clean_text(value).lower().strip(" .,/;:()[]{}<>\"'")
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0].split(":")[0]
    value = value.removeprefix("www.")
    return value


def website_from_domain(domain: str) -> str:
    domain = normalize_domain(domain)
    return f"https://{domain}/" if domain else ""


def valid_email(value: str) -> str:
    value = clean_text(value).lower().strip(" <>[](){}.,;:\"'")
    if not value or "*" in value or "개인정보" in value:
        return ""
    m = EMAIL_RE.fullmatch(value)
    if not m:
        return ""
    local, dom = value.split("@", 1)
    if dom in BLOCKED_EMAIL_DOMAINS or any(local.startswith(p) for p in BLOCKED_EMAIL_PREFIXES):
        return ""
    if dom.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
        return ""
    return value


def brand_from_domain(domain: str) -> str:
    d = normalize_domain(domain)
    if not d:
        return ""
    if d.endswith("smartstore.naver.com") or d.endswith("brand.naver.com"):
        return ""
    base = d.split(".")[0]
    return re.sub(r"[-_]", " ", base).strip().title()


def excluded(text: str) -> bool:
    t = clean_text(text).lower()
    return any(k.lower() in t for k in EXCLUDED_KEYWORDS | LARGE_BRAND_KEYWORDS)


def get(url: str, timeout: int = 20) -> requests.Response | None:
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200 and r.text:
                return r
            if r.status_code in (403, 429):
                time.sleep(2 + attempt * 2)
        except requests.RequestException:
            time.sleep(1 + attempt)
    return None


def extract_cafe24_domains(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    start_tokens = [
        "Website Sales Revenue Tech Spend Products Followers Employees Traffic Rank",
        "Website Sales Revenue Tech Spend",
    ]
    start = -1
    for token in start_tokens:
        start = text.find(token)
        if start >= 0:
            break
    if start >= 0:
        end_candidates = [x for x in (text.find("\ngoogle", start), text.find(" websites in this full report", start)) if x >= 0]
        end = min(end_candidates) if end_candidates else min(len(text), start + 15000)
        segment = text[start:end]
    else:
        segment = text[:20000]

    found: list[str] = []
    for match in DOMAIN_RE.finditer(segment):
        d = normalize_domain(match.group(1))
        if not d or d in BLOCKED_HOSTS or any(d.endswith("." + x) for x in BLOCKED_HOSTS):
            continue
        if d.startswith(("api.", "cdn.", "static.", "img.", "images.")):
            continue
        if d not in found:
            found.append(d)
    return found[:60]


def discover_cafe24_pages() -> list[tuple[str, str]]:
    main = "https://trends.builtwith.com/shop/Cafe24"
    pages: dict[str, str] = {
        "https://trends.builtwith.com/websitelist/Cafe24": "general",
        "https://trends.builtwith.com/websitelist/Cafe24/Added-Recently": "general",
        "https://trends.builtwith.com/websitelist/Cafe24/100-SKU-Products": "general",
        "https://trends.builtwith.com/websitelist/Cafe24/Low-Technology-Spend": "general",
        "https://trends.builtwith.com/websitelist/Cafe24/High-Technology-Spend": "general",
        "https://trends.builtwith.com/websitelist/Cafe24/10-Social-Followers": "general",
    }
    r = get(main)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(main, a["href"])
            if "/websitelist/Cafe24/commerce/" in href:
                slug = href.rstrip("/").split("/")[-1].lower()
                pages[href.split("?")[0]] = slug
            elif "/websitelist/Cafe24/" in href and "commerce" not in href:
                pages[href.split("?")[0]] = "general"
    for slug in CATEGORY_SLUGS:
        pages.setdefault(f"https://trends.builtwith.com/websitelist/Cafe24/commerce/{slug}", slug)
    return list(pages.items())


def scrape_cafe24() -> list[Prospect]:
    pages = discover_cafe24_pages()
    print(f"Cafe24 pages queued: {len(pages)}")
    rows: list[Prospect] = []

    def one(item: tuple[str, str]) -> tuple[str, str, list[str]]:
        url, slug = item
        r = get(url, timeout=25)
        return url, slug, extract_cafe24_domains(r.text) if r else []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for url, slug, domains in ex.map(one, pages):
            if domains:
                print(f"Cafe24 {slug}: {len(domains)}")
            label = CATEGORY_LABELS.get(slug, CATEGORY_LABELS["general"])
            for d in domains:
                if excluded(d):
                    continue
                brand = brand_from_domain(d)
                rows.append(
                    Prospect(
                        platform="Cafe24",
                        company_name=(brand or d) + " (상호 확인 필요)",
                        brand=brand or d,
                        email="",
                        description=f"Cafe24 기반 {label} 온라인 쇼핑몰 후보",
                        website=website_from_domain(d),
                        category=label,
                        region="대한민국(소재지 확인 필요)",
                        legal_type="확인 필요",
                        business_status="웹사이트 운영 후보",
                        source_url=url,
                        email_source_url="",
                        evidence="BuiltWith 공개 Cafe24 사용·상품 카테고리 목록",
                    )
                )
    # dedupe by host, preserving category-specific first hit
    out: dict[str, Prospect] = {}
    for p in rows:
        host = normalize_domain(p.website)
        out.setdefault(host, p)
    print(f"Cafe24 unique domains: {len(out)}")
    return list(out.values())


def wait_download(download_dir: Path, before: set[str], timeout: int = 90) -> Path | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = {p.name for p in download_dir.iterdir() if p.is_file()}
        new_names = current - before
        finished = [download_dir / n for n in new_names if not n.endswith((".crdownload", ".tmp"))]
        if finished and not any(p.suffix == ".crdownload" for p in download_dir.iterdir()):
            return max(finished, key=lambda p: p.stat().st_mtime)
        time.sleep(1)
    return None


def download_ftc_csvs() -> list[Path]:
    """Use a real browser because the FTC download page is JS-driven/403 to simple clients."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except Exception as e:
        print(f"Selenium unavailable: {e}")
        return []

    download_dir = (RAW / "ftc_downloads").resolve()
    download_dir.mkdir(parents=True, exist_ok=True)
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"--user-agent={UA}")
    opts.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    url = "https://www.ftc.go.kr/www/selectBizCommOpenList.do?key=255"
    paths: list[Path] = []
    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, 40)
        for city in FTC_CITIES:
            try:
                driver.get(url)
                city_el = wait.until(EC.presence_of_element_located((By.ID, "searchInst1")))
                city_sel = Select(city_el)
                try:
                    city_sel.select_by_visible_text(city)
                except Exception:
                    matches = [o for o in city_sel.options if city.replace("특별", "") in o.text.replace("특별", "")]
                    if not matches:
                        print(f"FTC city not found: {city}")
                        continue
                    city_sel.select_by_visible_text(matches[0].text)
                time.sleep(2)
                district_el = wait.until(EC.presence_of_element_located((By.ID, "searchInst2")))
                Select(district_el).select_by_index(0)
                before = {p.name for p in download_dir.iterdir() if p.is_file()}
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.md.primary.ico-down")))
                driver.execute_script("arguments[0].click();", button)
                p = wait_download(download_dir, before, timeout=90)
                if p:
                    target = RAW / f"FTC_{city}{p.suffix or '.csv'}"
                    shutil.copy2(p, target)
                    paths.append(target)
                    print(f"FTC downloaded {city}: {target.name} {target.stat().st_size:,} bytes")
                else:
                    print(f"FTC download timeout: {city}")
            except Exception as e:
                print(f"FTC {city} failed: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"FTC browser initialization failed: {type(e).__name__}: {e}")
    finally:
        if driver:
            driver.quit()
    return paths


def read_tabular(path: Path) -> pd.DataFrame | None:
    suffix = path.suffix.lower()
    if suffix in (".xls", ".xlsx"):
        try:
            return pd.read_excel(path, dtype=str)
        except Exception as e:
            print(f"read_excel failed {path}: {e}")
            return None
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        for sep in (",", "\t"):
            try:
                df = pd.read_csv(path, dtype=str, encoding=enc, sep=sep, engine="python")
                if len(df.columns) >= 5:
                    return df
            except Exception:
                pass
    print(f"Could not read {path}")
    return None


def pick_col(columns: Iterable[str], *needles: str) -> str | None:
    cols = [clean_text(c).replace(" ", "") for c in columns]
    originals = list(columns)
    for needle in needles:
        n = needle.replace(" ", "")
        for original, compact in zip(originals, cols):
            if n == compact or n in compact:
                return original
    return None


def normalize_store_url(value: str) -> str:
    v = clean_text(value)
    if not v:
        return ""
    if not re.match(r"(?i)^https?://", v):
        v = "https://" + v.lstrip("/")
    p = urlparse(v)
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/")
    if "smartstore.naver.com" in host or "brand.naver.com" in host or "storefarm.naver.com" in host:
        parts = [x for x in path.split("/") if x]
        if not parts:
            return ""
        return f"https://{host}/{parts[0]}"
    return v.rstrip("/")


def parse_ftc(paths: list[Path]) -> list[Prospect]:
    rows: list[Prospect] = []
    source = "https://www.ftc.go.kr/www/selectBizCommOpenList.do?key=255"
    for path in paths:
        df = read_tabular(path)
        if df is None or df.empty:
            continue
        print(f"FTC columns {path.name}: {list(df.columns)}")
        name_c = pick_col(df.columns, "상호", "업체명", "회사명")
        email_c = pick_col(df.columns, "전자우편", "이메일", "E-MAIL")
        domain_c = pick_col(df.columns, "인터넷도메인", "도메인", "홈페이지")
        region_c = pick_col(df.columns, "지역", "신고기관명", "사업장소재지", "주소")
        legal_c = pick_col(df.columns, "법인구분", "법인여부", "개인법인구분")
        status_c = pick_col(df.columns, "업소상태", "영업상태", "상태")
        if not name_c or not domain_c:
            print(f"FTC required columns missing in {path.name}")
            continue
        for _, r in df.iterrows():
            name = clean_text(r.get(name_c, ""))
            raw_domain = clean_text(r.get(domain_c, ""))
            if not raw_domain:
                continue
            lower = raw_domain.lower()
            if not any(x in lower for x in ("smartstore.naver.com", "brand.naver.com", "storefarm.naver.com")):
                continue
            website = normalize_store_url(raw_domain)
            if not website or excluded(name + " " + website):
                continue
            status = clean_text(r.get(status_c, "")) if status_c else ""
            if status and not any(x in status for x in ("정상", "영업", "통신판매")):
                continue
            store_slug = urlparse(website).path.strip("/").split("/")[0]
            platform = "네이버 브랜드스토어" if "brand.naver.com" in website else "네이버 스마트스토어"
            rows.append(
                Prospect(
                    platform=platform,
                    company_name=name or f"{store_slug} (상호 확인 필요)",
                    brand=store_slug or name,
                    email=valid_email(clean_text(r.get(email_c, ""))) if email_c else "",
                    description=f"{platform} 기반 온라인 판매 사업자",
                    website=website,
                    category="소매·온라인 쇼핑몰",
                    region=clean_text(r.get(region_c, "")) if region_c else "소재지 확인 필요",
                    legal_type=clean_text(r.get(legal_c, "")) if legal_c else "확인 필요",
                    business_status=status or "정상 영업 여부 확인 필요",
                    source_url=source,
                    email_source_url=source if valid_email(clean_text(r.get(email_c, ""))) else "",
                    evidence=f"공정거래위원회 공개 통신판매사업자 자료 ({path.name})",
                )
            )
    out: dict[str, Prospect] = {}
    for p in rows:
        out.setdefault(p.website.lower(), p)
    print(f"FTC SmartStore unique: {len(out)}")
    return list(out.values())


def page_metadata(p: Prospect) -> tuple[str, str, str, str]:
    """Return website, title, description, first public business email."""
    urls = [p.website]
    # For ordinary domains, add likely contact/company pages. Naver store roots are fetched once.
    host = urlparse(p.website).netloc.lower()
    if "naver.com" not in host:
        urls.extend(urljoin(p.website, x) for x in ("/shopinfo/company.html", "/member/privacy.html", "/contact", "/about"))
    title = ""
    desc = ""
    emails: list[str] = []
    for idx, url in enumerate(urls):
        r = get(url, timeout=12)
        if not r:
            continue
        soup = BeautifulSoup(r.text[:800000], "html.parser")
        if idx == 0:
            ogt = soup.find("meta", attrs={"property": "og:title"})
            ogd = soup.find("meta", attrs={"property": "og:description"})
            md = soup.find("meta", attrs={"name": re.compile("description", re.I)})
            title = clean_text((ogt or {}).get("content") if ogt else "")
            if not title and soup.title:
                title = clean_text(soup.title.get_text(" ", strip=True))
            desc = clean_text((ogd or {}).get("content") if ogd else "") or clean_text((md or {}).get("content") if md else "")
        for e in EMAIL_RE.findall(r.text):
            ve = valid_email(e)
            if ve and ve not in emails:
                emails.append(ve)
        if emails and title and desc:
            break
    return p.website, title[:160], desc[:360], emails[0] if emails else ""


def enrich(prospects: list[Prospect], max_sites: int = 1800) -> list[Prospect]:
    # Prioritize Naver records and Cafe24 records without verified email.
    targets = prospects[:max_sites]
    print(f"Enriching public metadata/email for {len(targets)} sites")
    results: dict[str, tuple[str, str, str]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=28) as ex:
        futures = {ex.submit(page_metadata, p): p.website for p in targets}
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            try:
                website, title, desc, email = fut.result()
                results[website] = (title, desc, email)
            except Exception:
                pass
            done += 1
            if done % 100 == 0:
                print(f"Enriched {done}/{len(targets)}")

    for p in prospects:
        title, desc, email = results.get(p.website, ("", "", ""))
        if title:
            clean_title = re.sub(r"\s*[-|:]\s*(네이버 스마트스토어|NAVER|공식몰).*$", "", title, flags=re.I).strip()
            if clean_title and len(clean_title) <= 80:
                p.brand = clean_title
                if p.company_name.endswith("(상호 확인 필요)"):
                    p.company_name = clean_title + " (상호 확인 필요)"
        if desc and len(desc) >= 12:
            p.description = desc
        if not p.email and email:
            p.email = email
            p.email_source_url = p.website
            p.evidence += "; 공식 웹사이트 공개 이메일 확인"
    return prospects


def dedupe_and_rank(items: list[Prospect]) -> list[Prospect]:
    # Platform priority: SmartStore then Cafe24. Valid emails first within each group.
    dedup: dict[str, Prospect] = {}
    for p in items:
        key = p.website.lower().rstrip("/")
        if not key or excluded(p.company_name + " " + p.description + " " + p.website):
            continue
        existing = dedup.get(key)
        if existing is None or (not existing.email and p.email):
            dedup[key] = p
    rows = list(dedup.values())
    def score(p: Prospect) -> tuple:
        return (
            0 if p.platform.startswith("네이버") else 1,
            0 if p.email else 1,
            0 if p.company_name and "확인 필요" not in p.company_name else 1,
            p.company_name.lower(),
        )
    rows.sort(key=score)
    return rows


def save(rows: list[Prospect]) -> None:
    data = [asdict(p) for p in rows]
    with open(OUT / "prospects.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(OUT / "prospects.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()) if data else list(Prospect.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(data)
    stats = {
        "total": len(rows),
        "with_email": sum(bool(x.email) for x in rows),
        "smartstore": sum(x.platform.startswith("네이버") for x in rows),
        "cafe24": sum(x.platform == "Cafe24" for x in rows),
        "by_platform": {},
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    for p in rows:
        stats["by_platform"][p.platform] = stats["by_platform"].get(p.platform, 0) + 1
    with open(OUT / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def main() -> int:
    cafe = scrape_cafe24()
    ftc_paths = download_ftc_csvs()
    smart = parse_ftc(ftc_paths)
    rows = dedupe_and_rank(smart + cafe)
    # Metadata crawl can be disabled for a quick retry via ENRICH=0.
    if os.environ.get("ENRICH", "1") != "0":
        rows = enrich(rows, max_sites=int(os.environ.get("MAX_ENRICH", "1800")))
        rows = dedupe_and_rank(rows)
    save(rows)
    if len(rows) < 900:
        print(f"WARNING: only {len(rows)} unique prospects generated", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
