#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import shutil
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from smoody_full_ftc_extract import (
    DB, OUT, RAW, REGIONS, SOURCE_PAGE, export_table, init_db, process_file
)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
DOWNLOAD_DIR = (RAW / "browser_downloads").resolve()
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def new_driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"--user-agent={UA}")
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
    })
    driver = webdriver.Chrome(options=opts)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_DIR)})
    except Exception:
        pass
    return driver


def clear_downloads():
    for p in DOWNLOAD_DIR.iterdir():
        if p.is_file():
            try: p.unlink()
            except Exception: pass


def wait_download(timeout=300):
    deadline = time.time() + timeout
    stable = None
    stable_size = -1
    stable_count = 0
    while time.time() < deadline:
        files = [p for p in DOWNLOAD_DIR.iterdir() if p.is_file()]
        partial = [p for p in files if p.name.endswith((".crdownload", ".tmp"))]
        complete = [p for p in files if p not in partial and p.stat().st_size > 1000]
        if complete and not partial:
            candidate = max(complete, key=lambda p: p.stat().st_mtime)
            size = candidate.stat().st_size
            if stable == candidate and stable_size == size:
                stable_count += 1
            else:
                stable, stable_size, stable_count = candidate, size, 0
            if stable_count >= 2:
                return candidate
        time.sleep(1)
    return None


def download_region(driver, wait, region):
    clear_downloads()
    driver.get(SOURCE_PAGE)
    city_el = wait.until(EC.presence_of_element_located((By.ID, "searchInst1")))
    city = Select(city_el)
    try:
        city.select_by_visible_text(region)
    except Exception:
        # Legacy fallbacks are only needed for old regional labels.
        fallback = {"강원특별자치도": "강원도", "전북특별자치도": "전라북도"}.get(region)
        if not fallback:
            raise
        city.select_by_visible_text(fallback)
    time.sleep(2)
    district_el = wait.until(EC.presence_of_element_located((By.ID, "searchInst2")))
    Select(district_el).select_by_index(0)
    time.sleep(1)
    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.md.primary.ico-down")))
    driver.execute_script("arguments[0].click();", button)
    downloaded = wait_download(360)
    if not downloaded:
        return None
    target = RAW / f"{region}.csv"
    if target.exists(): target.unlink()
    shutil.move(str(downloaded), str(target))
    return target


def main():
    con = init_db()
    logs = []
    driver = new_driver()
    wait = WebDriverWait(driver, 45)
    try:
        for region, _aliases in REGIONS:
            try:
                path = download_region(driver, wait, region)
                if not path:
                    logs.append({"region": region, "status": "download_failed"})
                    print("DOWNLOAD_FAILED", region, flush=True)
                    continue
                size = path.stat().st_size
                print("DOWNLOADED", region, size, path.name, flush=True)
                stats = process_file(con, path, region, SOURCE_PAGE)
                logs.append({"region": region, "status": "ok", "bytes": size, **dict(stats)})
                try: path.unlink()
                except Exception: pass
            except Exception as e:
                logs.append({"region": region, "status": "failed", "error": repr(e)})
                print("REGION_ERROR", region, repr(e), flush=True)
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = new_driver()
                wait = WebDriverWait(driver, 45)
    finally:
        try: driver.quit()
        except Exception: pass

    confirmed_count = export_table(con,
        "SELECT platform,company_name,brand,public_email,email_status,description,website,category,items,region,legal_type,report_date,report_no,business_status,confidence,ai_scenario,contact_priority,source_url,source_file,extracted_at FROM confirmed ORDER BY CASE WHEN public_email<>'' THEN 0 ELSE 1 END,platform,region,company_name",
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
