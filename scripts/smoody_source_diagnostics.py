#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, time
from pathlib import Path
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

OUT=Path('research_diag_output'); OUT.mkdir(exist_ok=True)
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept-Language':'ko-KR,ko;q=0.9,en;q=0.7'})

urls={
 'ftc':'https://www.ftc.go.kr/www/selectBizCommOpenList.do?key=255',
 'data_search':'https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword='+quote('통신판매사업자'),
 'localdata':'https://www.localdata.go.kr/lif/lifeCtacDataView.do?opnSvcId=08_26_04_P',
 'localdata_file':'https://file.localdata.go.kr/file/ecommerce_businesses/info',
 'builtwith':'https://trends.builtwith.com/websitelist/Cafe24',
 'commoncrawl':'https://index.commoncrawl.org/collinfo.json',
 'naver_search':'https://search.naver.com/search.naver?query='+quote('site:smartstore.naver.com 수제'),
 'bing_search':'https://www.bing.com/search?q='+quote('site:smartstore.naver.com 수제'),
}
summary={}
for name,url in urls.items():
    try:
        r=s.get(url,timeout=40,allow_redirects=True)
        summary[name]={'status':r.status_code,'url':r.url,'length':len(r.content),'content_type':r.headers.get('content-type',''),'headers':dict(r.headers)}
        (OUT/f'{name}.html').write_bytes(r.content)
    except Exception as e:
        summary[name]={'error':repr(e)}

# Inspect links/forms in request version of FTC and data/localdata pages.
for name in ('ftc','data_search','localdata','localdata_file'):
    p=OUT/f'{name}.html'
    if not p.exists(): continue
    try:
        text=p.read_text('utf-8',errors='replace')
        soup=BeautifulSoup(text,'html.parser')
        items=[]
        for tag in soup.find_all(['form','a','button','select','option','input','script']):
            attrs={k:str(v)[:500] for k,v in tag.attrs.items() if k in ('id','name','class','href','src','action','method','onclick','value','data-url','data-file','download')}
            txt=' '.join(tag.get_text(' ',strip=True).split())[:300]
            if attrs or txt:
                items.append({'tag':tag.name,'attrs':attrs,'text':txt})
        (OUT/f'{name}_elements.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),'utf-8')
    except Exception as e:
        summary[name+'_parse']={'error':repr(e)}

# Common Crawl sample query if collection list works.
try:
    cc=json.loads((OUT/'commoncrawl.html').read_text('utf-8',errors='replace'))
    latest=cc[0]['id']
    summary['commoncrawl_latest']=latest
    for target,key in [('*.cafe24.com','cc_cafe24'),('smartstore.naver.com/*','cc_smartstore')]:
        u=f'https://index.commoncrawl.org/{latest}-index?url={quote(target,safe="*")}&output=json&filter=status:200&collapse=urlkey&pageSize=100'
        rr=s.get(u,timeout=60)
        summary[key]={'status':rr.status_code,'url':rr.url,'length':len(rr.content),'content_type':rr.headers.get('content-type','')}
        (OUT/f'{key}.txt').write_bytes(rr.content)
except Exception as e:
    summary['commoncrawl_query']={'error':repr(e)}

# Browser diagnostics and network capture for FTC.
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    opts=webdriver.ChromeOptions(); opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox'); opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1920,1080'); opts.add_argument(f'--user-agent={UA}')
    opts.set_capability('goog:loggingPrefs',{'performance':'ALL','browser':'ALL'})
    d=webdriver.Chrome(options=opts)
    d.get(urls['ftc']); time.sleep(4)
    (OUT/'ftc_browser.html').write_text(d.page_source,'utf-8')
    d.save_screenshot(str(OUT/'ftc_browser.png'))
    elements=[]
    for el in d.find_elements(By.CSS_SELECTOR,'form,a,button,select,option,input,script'):
        try:
            elements.append({'tag':el.tag_name,'id':el.get_attribute('id'),'name':el.get_attribute('name'),'class':el.get_attribute('class'),'href':el.get_attribute('href'),'src':el.get_attribute('src'),'action':el.get_attribute('action'),'method':el.get_attribute('method'),'onclick':el.get_attribute('onclick'),'value':el.get_attribute('value'),'text':el.text[:300]})
        except: pass
    (OUT/'ftc_browser_elements.json').write_text(json.dumps(elements,ensure_ascii=False,indent=2),'utf-8')
    summary['ftc_browser']={'title':d.title,'url':d.current_url,'html_length':len(d.page_source),'elements':len(elements)}
    # Select first non-placeholder city, then try click download.
    try:
        sel=Select(WebDriverWait(d,20).until(EC.presence_of_element_located((By.ID,'searchInst1'))))
        summary['ftc_city_options']=[{'text':o.text,'value':o.get_attribute('value')} for o in sel.options]
        if len(sel.options)>1: sel.select_by_index(1)
        time.sleep(3)
        buttons=d.find_elements(By.CSS_SELECTOR,'a.btn.md.primary.ico-down,button,input[type=button],a[onclick*="down"],a[onclick*="file"]')
        summary['ftc_click_candidates']=[{'tag':x.tag_name,'text':x.text,'id':x.get_attribute('id'),'class':x.get_attribute('class'),'onclick':x.get_attribute('onclick'),'href':x.get_attribute('href')} for x in buttons]
        for x in buttons:
            if '다운' in x.text or 'down' in (x.get_attribute('class') or '').lower() or 'down' in (x.get_attribute('onclick') or '').lower():
                try: d.execute_script('arguments[0].click();',x); time.sleep(6); break
                except: pass
        logs=d.get_log('performance')
        net=[]
        for item in logs:
            try:
                msg=json.loads(item['message'])['message']
                if msg['method'] in ('Network.requestWillBeSent','Network.responseReceived'):
                    p=msg['params']; req=p.get('request',{}); resp=p.get('response',{})
                    net.append({'method':msg['method'],'url':req.get('url') or resp.get('url'),'httpMethod':req.get('method'),'postData':req.get('postData'),'status':resp.get('status'),'mimeType':resp.get('mimeType')})
            except: pass
        (OUT/'ftc_network.json').write_text(json.dumps(net,ensure_ascii=False,indent=2),'utf-8')
        (OUT/'ftc_browser_log.json').write_text(json.dumps(d.get_log('browser'),ensure_ascii=False,indent=2),'utf-8')
    except Exception as e:
        summary['ftc_browser_interaction']={'error':repr(e)}
    d.quit()
except Exception as e:
    summary['selenium']={'error':repr(e)}

(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
