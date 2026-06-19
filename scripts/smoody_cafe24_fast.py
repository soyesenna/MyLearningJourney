#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import csv
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OUT = Path("research_fast_output")
OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.6"})

EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])([a-z0-9][a-z0-9._%+\-]{0,63}@[a-z0-9][a-z0-9.\-]{1,190}\.[a-z]{2,24})(?![\w.-])")
DOMAIN_RE = re.compile(r"(?i)(?<![@\w-])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:co\.kr|or\.kr|go\.kr|ne\.kr|re\.kr|pe\.kr|kr|com|net|org|shop|store|io|life|world|global|co|me|biz|info|company|market|design|studio|today|care|beauty|fashion|online))(?![\w-])")
HANGUL_RE = re.compile(r"[가-힣]")

BLOCK_HOSTS = {"builtwith.com","trends.builtwith.com","pro.builtwith.com","google.com","facebook.com","instagram.com","youtube.com","twitter.com","x.com","linkedin.com","pinterest.com","cloudflare.com","w3.org","schema.org","jquery.com","naver.com","pstatic.net"}
BAD_EMAIL_DOMAINS = {"example.com","sentry.io","wixpress.com","google.com","domain.com","email.com"}
BAD_EMAIL_PREFIX = ("noreply","no-reply","donotreply","do-not-reply","abuse","postmaster","webmaster","privacy","security")
EXCLUDED = ("전자담배","담배","성인용","카지노","도박","슬롯","바카라","약국","병원","의원","치과","의료","보험","대출","부동산","법무","세무","회계","점술","사주","안마","유흥")
LARGE = ("삼성전자","엘지전자","lg전자","롯데","신세계","현대백화점","아모레퍼시픽","쿠팡","다이소","이랜드")

CATEGORIES = {
"watches":"시계·액세서리","vitamins":"건강·영양 제품","shoes":"신발","skin-care":"스킨케어·뷰티","skincare":"스킨케어·뷰티","photography":"사진·촬영용품","luggage":"여행가방·여행용품","dinnerware":"식기·테이블웨어","activewear":"스포츠·액티브웨어","lingerie":"이너웨어","instruments":"악기·음향용품","nail-care":"네일·뷰티","nailcare":"네일·뷰티","tennis":"테니스·스포츠용품","home-decor":"홈데코·인테리어","computers":"컴퓨터·디지털","salons":"헤어·살롱용품","furniture":"가구·리빙","sewing":"봉제·공예용품","golf":"골프용품","jewellery":"주얼리·액세서리","jewelry":"주얼리·액세서리","groceries-and-food":"식품·그로서리","food-and-groceries":"식품·그로서리","fragrance":"향수·향 제품","cycling":"자전거·사이클용품","appliances":"생활가전","coats-and-jackets":"패션·아우터","underwear":"이너웨어","apparel":"패션·의류","nutrition":"식품·영양 제품","books":"도서·문구","eyewear":"안경·아이웨어","fashion":"패션·잡화","makeup":"메이크업·뷰티","hair-care":"헤어케어·뷰티","haircare":"헤어케어·뷰티","womens-clothing":"여성의류","coffee":"커피·음료","tableware":"주방·테이블웨어","swimwear":"수영복·레저웨어","party-supplies":"파티·행사용품","bags":"가방·잡화","phones":"휴대폰·모바일 액세서리","fitness":"피트니스·운동용품","kitchenware":"주방용품","general":"온라인 쇼핑몰"
}


def clean(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()


def host(v):
    v=clean(v).lower(); v=re.sub(r"^https?://", "", v); return v.split("/")[0].split(":")[0].removeprefix("www.").strip(" .")


def get(url, timeout=8):
    try:
        r=S.get(url,timeout=timeout,allow_redirects=True)
        if r.status_code==200 and r.text: return r
    except requests.RequestException:
        return None
    return None


def valid_email(v):
    v=clean(v).lower().strip(" <>[](){}.,;:\"'")
    if not EMAIL_RE.fullmatch(v) or "*" in v: return ""
    local,dom=v.split("@",1)
    if dom in BAD_EMAIL_DOMAINS or local.startswith(BAD_EMAIL_PREFIX): return ""
    if dom.endswith((".png",".jpg",".jpeg",".gif",".svg",".webp")): return ""
    return v


def domains_from(html):
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_text("\n",strip=True)
    start=text.find("Website Sales Revenue Tech Spend")
    segment=text[start:] if start>=0 else text[:25000]
    end=segment.find(" websites in this full report")
    if end>0: segment=segment[:end]
    out=[]
    for m in DOMAIN_RE.finditer(segment):
        d=host(m.group(1))
        if not d or d in BLOCK_HOSTS or any(d.endswith("."+x) for x in BLOCK_HOSTS): continue
        if d.startswith(("api.","cdn.","static.","img.","images.")): continue
        if d not in out: out.append(d)
    return out[:60]


def discover_pages():
    pages={"https://trends.builtwith.com/websitelist/Cafe24":"general","https://trends.builtwith.com/websitelist/Cafe24/Added-Recently":"general","https://trends.builtwith.com/websitelist/Cafe24/100-SKU-Products":"general","https://trends.builtwith.com/websitelist/Cafe24/Low-Technology-Spend":"general","https://trends.builtwith.com/websitelist/Cafe24/10-Social-Followers":"general"}
    r=get("https://trends.builtwith.com/shop/Cafe24",12)
    if r:
        soup=BeautifulSoup(r.text,"html.parser")
        for a in soup.find_all("a",href=True):
            u=urljoin(r.url,a["href"]).split("?")[0]
            if "/websitelist/Cafe24/commerce/" in u:
                pages[u]=u.rstrip("/").split("/")[-1].lower()
    for slug in CATEGORIES:
        pages.setdefault(f"https://trends.builtwith.com/websitelist/Cafe24/commerce/{slug}",slug)
    return list(pages.items())


def scrape_candidates():
    pages=discover_pages(); found={}
    def one(item):
        u,slug=item; r=get(u,12); return u,slug,domains_from(r.text) if r else []
    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as ex:
        for u,slug,ds in ex.map(one,pages):
            print(slug,len(ds),flush=True)
            for d in ds:
                found.setdefault(d,{"platform":"Cafe24","website":f"https://{d}/","category":CATEGORIES.get(slug,"온라인 쇼핑몰"),"source_url":u})
    return list(found.values())


def enrich(item):
    website=item["website"]
    urls=[website,urljoin(website,"/shopinfo/company.html"),urljoin(website,"/member/privacy.html")]
    title=desc=email=""; email_url=""
    all_text=""
    for idx,u in enumerate(urls):
        r=get(u,6)
        if not r: continue
        html=r.text[:700000]; soup=BeautifulSoup(html,"html.parser")
        text=soup.get_text(" ",strip=True); all_text += " "+text[:8000]
        if idx==0:
            ogt=soup.find("meta",attrs={"property":"og:title"}); ogd=soup.find("meta",attrs={"property":"og:description"}); md=soup.find("meta",attrs={"name":re.compile("description",re.I)})
            title=clean(ogt.get("content") if ogt and ogt.get("content") else (soup.title.get_text(" ",strip=True) if soup.title else ""))[:140]
            desc=clean(ogd.get("content") if ogd and ogd.get("content") else (md.get("content") if md and md.get("content") else ""))[:360]
        for e in EMAIL_RE.findall(html):
            ve=valid_email(e)
            if ve: email=ve; email_url=u; break
        if email and title and desc: break
    d=host(website); base=re.sub(r"[-_]"," ",d.split(".")[0]).title()
    title=re.sub(r"\s*[-|:]\s*(NAVER|공식몰|쇼핑몰).*$","",title,flags=re.I).strip()
    brand=title if title and len(title)<=80 and "카페24" not in title.lower() else base
    if any(x.lower() in (brand+" "+desc+" "+all_text).lower() for x in EXCLUDED+LARGE): return None
    # Keep Korean-facing domains/content; allow .kr domains even if metadata is sparse.
    if not (d.endswith((".kr",".co.kr",".or.kr")) or HANGUL_RE.search(brand+desc+all_text)):
        return None
    item.update({"company_name":brand,"brand":brand,"email":email,"description":desc or f"Cafe24 기반 {item['category']} 온라인 쇼핑몰 후보","region":"대한민국(소재지 확인 필요)","legal_type":"확인 필요","business_status":"웹사이트 운영 후보","email_source_url":email_url,"evidence":"BuiltWith 공개 Cafe24 사용 목록; 공식 웹사이트 공개정보 확인"})
    return item


def main():
    rows=scrape_candidates(); print("unique",len(rows),flush=True)
    max_enrich=int(os.environ.get("MAX_ENRICH","1600")); rows=rows[:max_enrich]
    out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=45) as ex:
        for i,r in enumerate(ex.map(enrich,rows),1):
            if r: out.append(r)
            if i%100==0: print("enriched",i,"kept",len(out),flush=True)
    out.sort(key=lambda x:(0 if x.get("email") else 1,x.get("company_name","").lower()))
    fields=["platform","company_name","brand","email","description","website","category","region","legal_type","business_status","source_url","email_source_url","evidence"]
    with open(OUT/"prospects.csv","w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:r.get(k,"") for k in fields} for r in out])
    with open(OUT/"prospects.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    stats={"total":len(out),"with_email":sum(bool(x.get("email")) for x in out),"cafe24":len(out),"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    with open(OUT/"stats.json","w",encoding="utf-8") as f: json.dump(stats,f,ensure_ascii=False,indent=2)
    print(json.dumps(stats,ensure_ascii=False),flush=True)
    return 0 if len(out)>=900 else 2

if __name__=="__main__": raise SystemExit(main())
