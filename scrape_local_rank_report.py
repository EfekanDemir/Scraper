import json
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import Playwright, sync_playwright, Response


TARGET_URL_DEFAULT = "https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb"
OUTPUT_XLSX_DEFAULT = "local_rank_report_data.xlsx"


def safe_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return " ".join(value.split())


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def collect_headings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            rows.append(
                {
                    "level": level,
                    "text": safe_text(tag.get_text(" ", strip=True)),
                    "id": tag.get("id", ""),
                    "classes": " ".join(tag.get("class", []) or []),
                }
            )
    return rows


def collect_links(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for a in soup.find_all("a"):
        rows.append(
            {
                "text": safe_text(a.get_text(" ", strip=True)),
                "href": a.get("href", ""),
                "rel": a.get("rel", []),
                "target": a.get("target", ""),
            }
        )
    return rows


def collect_images(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for img in soup.find_all("img"):
        rows.append(
            {
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
            }
        )
    return rows


def collect_tables(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    table_index = 0
    for tbl in soup.find_all("table"):
        headers: List[str] = []
        thead = tbl.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = [safe_text(th.get_text(" ", strip=True)) for th in header_row.find_all(["th", "td"])]
        if not headers:
            first_tr = tbl.find("tr")
            if first_tr:
                headers = [safe_text(th.get_text(" ", strip=True)) for th in first_tr.find_all(["th", "td"])]
        body_rows = tbl.find_all("tr")
        row_idx = -1
        for r in body_rows:
            cells = r.find_all(["th", "td"])
            if not cells:
                continue
            row_idx += 1
            for col_idx, cell in enumerate(cells):
                cell_text = safe_text(cell.get_text(" ", strip=True))
                header_val = headers[col_idx] if col_idx < len(headers) else ""
                rows.append(
                    {
                        "table_index": table_index,
                        "row_index": row_idx,
                        "col_index": col_idx,
                        "header": header_val,
                        "value": cell_text,
                    }
                )
        table_index += 1
    return rows


def collect_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    section_like_selectors = [
        "section",
        "article",
        "div[role='region']",
        "div[class*='section']",
        "div[class*='card']",
        "div[class*='panel']",
        "div[class*='box']",
    ]
    seen = set()
    for sel in section_like_selectors:
        for el in soup.select(sel):
            key = id(el)
            if key in seen:
                continue
            seen.add(key)
            text = safe_text(el.get_text(" ", strip=True))
            if not text:
                continue
            header_el = None
            for h in el.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                header_el = h
                break
            rows.append(
                {
                    "selector": sel,
                    "header": safe_text(header_el.get_text(" ", strip=True)) if header_el else "",
                    "text": text,
                    "classes": " ".join(el.get("class", []) or []),
                    "id": el.get("id", ""),
                }
            )
    return rows


def collect_popups_and_tooltips(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    selectors = [
        "[role='dialog']",
        ".modal, .Modal, .popup, .Popover, .tooltip, .Tooltip, [data-testid*='modal'], [data-testid*='dialog']",
        "[role='tooltip']",
    ]
    seen = set()
    for sel in selectors:
        for el in soup.select(sel):
            key = id(el)
            if key in seen:
                continue
            seen.add(key)
            text = safe_text(el.get_text(" ", strip=True))
            if not text:
                continue
            html_raw = el.decode() if hasattr(el, "decode") else str(el)
            rows.append(
                {
                    "selector": sel,
                    "text": text,
                    "html": html_raw[:32000],  # avoid over-large cells
                }
            )
    return rows


def collect_meta_tags(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for meta in soup.find_all("meta"):
        rows.append(
            {
                "name": meta.get("name", meta.get("property", "")),
                "property": meta.get("property", ""),
                "content": meta.get("content", ""),
                "charset": meta.get("charset", ""),
            }
        )
    return rows


def recursively_find_geo(obj: Any, path: str = "") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    def norm_key(k: str) -> str:
        return (k or "").lower()

    def pick(v: Dict[str, Any], keys: List[str]) -> Optional[Any]:
        for k in keys:
            if k in v and v[k] is not None:
                return v[k]
        return None

    if isinstance(obj, dict):
        lowered = {norm_key(k): v for k, v in obj.items()}
        lat = pick(lowered, ["lat", "latitude", "y"])
        lng = pick(lowered, ["lng", "lon", "long", "longitude", "x"])
        if lat is None and isinstance(lowered.get("location"), dict):
            lat = pick({k: lowered["location"].get(k) for k in lowered["location"] or {}}, ["lat", "latitude"])
            lng = pick({k: lowered["location"].get(k) for k in lowered["location"] or {}}, ["lng", "lon", "long", "longitude"])
        if lat is None and isinstance(lowered.get("geometry"), dict):
            loc = lowered.get("geometry", {}).get("location")
            if isinstance(loc, dict):
                lat = pick({k: loc.get(k) for k in loc or {}}, ["lat", "latitude"])
                lng = pick({k: loc.get(k) for k in loc or {}}, ["lng", "lon", "long", "longitude"])
        if lat is not None and lng is not None:
            name = pick(lowered, ["name", "title", "label", "place_name", "business_name"]) or ""
            address = pick(lowered, ["address", "formatted_address", "addr", "vicinity"]) or ""
            rows.append({
                "path": path,
                "name": str(name),
                "address": str(address),
                "lat": lat,
                "lng": lng,
                "snippet": json.dumps(obj, ensure_ascii=False)[:2000],
            })
        for k, v in obj.items():
            rows.extend(recursively_find_geo(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(obj, list):
        for idx, it in enumerate(obj):
            rows.extend(recursively_find_geo(it, f"{path}[{idx}]"))
    return rows


def collect_dom_map_like(page) -> List[Dict[str, Any]]:
    # Try to extract visible map-related DOM nodes (Leaflet popups, markers)
    try:
        dom_data = page.evaluate(
            """
            () => {
              const rows = [];
              // Leaflet markers
              document.querySelectorAll('.leaflet-marker-icon, .leaflet-marker-shadow').forEach((el, i) => {
                rows.push({ kind: 'leaflet-marker', index: i, title: el.getAttribute('title')||'', alt: el.getAttribute('alt')||'', html: el.outerHTML.substring(0, 1000) });
              });
              // Leaflet popups
              document.querySelectorAll('.leaflet-popup-content').forEach((el, i) => {
                rows.push({ kind: 'leaflet-popup', index: i, text: (el.textContent||'').trim(), html: el.outerHTML.substring(0, 2000) });
              });
              // Map containers
              document.querySelectorAll('#map, [id*="map"], .map, .gm-style, .leaflet-container').forEach((el, i) => {
                rows.push({ kind: 'map-container', index: i, classes: el.className||'', id: el.id||'', html: el.outerHTML.substring(0, 1000) });
              });
              return rows.slice(0, 500);
            }
            """
        )
        return dom_data or []
    except Exception:
        return []


def collect_inline_and_global_json(page) -> List[Dict[str, Any]]:
    try:
        payloads = page.evaluate(
            """
            () => {
              const res = [];
              const push = (source, jsonString) => {
                if (!jsonString) return;
                try {
                  const trimmed = jsonString.trim();
                  if (!trimmed) return;
                  res.push({ source, json: trimmed });
                } catch(e) {}
              };
              // Script tags with JSON
              const scripts = Array.from(document.querySelectorAll('script'));
              for (const s of scripts) {
                const type = (s.type||'').toLowerCase();
                if (type.includes('application/json') || type.includes('ld+json')) {
                  push('script:'+ (type||'application/json'), s.textContent||'');
                }
              }
              // Common global containers
              const keys = Object.getOwnPropertyNames(window).filter(k => /(__NEXT_DATA__|__APOLLO_STATE__|__NUXT__|__INITIAL_STATE__|STATE|DATA|map|maps|markers|places|results|bootstrap|preload)/i.test(k));
              for (const k of keys) {
                try {
                  const v = window[k];
                  if (v && (typeof v === 'object' || Array.isArray(v))) {
                    push('window.'+k, JSON.stringify(v));
                  }
                } catch(e) {}
              }
              return res.slice(0, 300);
            }
            """
        )
        return payloads or []
    except Exception:
        return []


def scroll_page(page, step_px: int = 600, max_rounds: int = 40, wait_ms: int = 400):
    last_height = 0
    for _ in range(max_rounds):
        page.evaluate("n => window.scrollBy(0, n)", step_px)
        time.sleep(wait_ms / 1000.0)
        height = page.evaluate("document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height


def click_all_interactives(page) -> None:
    candidates_selectors = [
        "button",
        "[role='button']",
        "[aria-haspopup='dialog']",
        "[aria-expanded='false']",
        "[data-testid*='tab']",
        "[role='tab']",
        "[data-action*='expand']",
        "[data-action*='open']",
        "[data-action*='details']",
    ]
    text_keywords = [
        "expand", "show", "more", "details", "detay", "göster", "devam", "open", "view", "info", "?",
    ]

    clicked = 0
    # Click all tabs first to reveal hidden panels
    for sel in ["[role='tab']", "[data-testid*='tab']"]:
        for el in page.query_selector_all(sel):
            try:
                el.click(timeout=1000)
                clicked += 1
                page.wait_for_timeout(200)
            except Exception:
                continue

    # Click buttons with meaningful text
    for sel in ["button", "[role='button']"]:
        for el in page.query_selector_all(sel):
            try:
                txt = (el.inner_text(timeout=500) or "").lower()
            except Exception:
                txt = ""
            if any(k in txt for k in text_keywords):
                try:
                    el.click(timeout=1000)
                    clicked += 1
                    page.wait_for_timeout(250)
                except Exception:
                    continue

    # Click remaining candidates by attribute heuristics
    for sel in candidates_selectors:
        for el in page.query_selector_all(sel):
            try:
                el.click(timeout=750)
                clicked += 1
                page.wait_for_timeout(150)
            except Exception:
                continue

    # Try to accept cookie banners if present
    for label in ["accept", "kabul", "tamam", "allow", "agree", "onayla"]:
        try:
            btn = page.get_by_role("button", name=lambda s: s and label in s.lower())
            if btn:
                btn.click(timeout=800)
                clicked += 1
                page.wait_for_timeout(250)
        except Exception:
            pass


class NetworkCollector:
    def __init__(self, size_limit_bytes: int = 5 * 1024 * 1024):
        self.json_payloads: List[Dict[str, Any]] = []
        self.size_limit = size_limit_bytes

    def handle_response(self, response: Response):
        try:
            ct = response.headers.get("content-type", "").lower()
            url = response.url
            if "application/json" in ct or url.endswith(".json"):
                body = response.body()
                if body and len(body) <= self.size_limit:
                    try:
                        data = json.loads(body.decode("utf-8", errors="ignore"))
                    except Exception:
                        data = {"raw": body.decode("utf-8", errors="ignore")}
                    self.json_payloads.append(
                        {
                            "url": url,
                            "status": response.status,
                            "json": json.dumps(data, ensure_ascii=False),
                        }
                    )
        except Exception:
            # swallow to avoid breaking scraping
            pass


def run_scrape(url: str, out_xlsx: str) -> Tuple[bool, str]:
    meta_info: Dict[str, Any] = {"startedAt": now_iso(), "url": url}
    network = NetworkCollector()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])  # headless for CI
            context = browser.new_context(
                viewport={"width": 1400, "height": 1000},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                ),
                ignore_https_errors=True,
                java_script_enabled=True,
            )
            page = context.new_page()

            page.on("response", network.handle_response)

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)

            # Interaction phase to reveal hidden content
            scroll_page(page, step_px=700, max_rounds=50, wait_ms=350)
            click_all_interactives(page)
            scroll_page(page, step_px=700, max_rounds=20, wait_ms=300)
            page.wait_for_timeout(1200)

            # Try opening any info/help buttons by common selectors
            for sel in ["[aria-label*='info']", "[title*='info']", "[title*='detay']", "[aria-label*='yardım']"]:
                for el in page.query_selector_all(sel):
                    try:
                        el.click(timeout=600)
                        page.wait_for_timeout(200)
                    except Exception:
                        pass

            # Final settle
            page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(1.0)

            # Snapshot HTML after interactions
            html = page.content()
            title = page.title()
            meta_info.update({"pageTitle": title, "finishedAt": now_iso()})

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            headings = collect_headings(soup)
            links = collect_links(soup)
            images = collect_images(soup)
            tables = collect_tables(soup)
            sections = collect_sections(soup)
            popups = collect_popups_and_tooltips(soup)
            metas = collect_meta_tags(soup)

            # Capture inline/global JSON and DOM map-like artifacts
            inline_json_payloads = collect_inline_and_global_json(page)
            dom_map_like = collect_dom_map_like(page)

            # Also capture full body text once
            body = soup.find("body")
            raw_text_rows = []
            if body:
                raw_text = safe_text(body.get_text(" ", strip=True))
                if raw_text:
                    # Split long text into chunks to avoid Excel cell limits
                    chunk_size = 30000
                    for i in range(0, len(raw_text), chunk_size):
                        raw_text_rows.append({"chunk_index": i // chunk_size, "text": raw_text[i : i + chunk_size]})

            # Build MapData by recursively finding lat/lng in inline JSON first
            map_rows: List[Dict[str, Any]] = []
            for p in inline_json_payloads:
                try:
                    data_obj = json.loads(p.get("json") or "null")
                    geo_rows = recursively_find_geo(data_obj, path=p.get("source", "inline"))
                    for r in geo_rows:
                        r["source"] = p.get("source", "inline")
                    map_rows.extend(geo_rows)
                except Exception:
                    continue
            # Also mine network JSON bodies (will append later after df_network is built)
            df_map = pd.DataFrame(map_rows)

            # Build DataFrames
            df_meta = pd.DataFrame([{**meta_info}])
            df_headings = pd.DataFrame(headings)
            df_sections = pd.DataFrame(sections)
            df_tables = pd.DataFrame(tables)
            df_links = pd.DataFrame(links)
            df_images = pd.DataFrame(images)
            df_popups = pd.DataFrame(popups)
            df_network = pd.DataFrame(network.json_payloads)
            df_raw_text = pd.DataFrame(raw_text_rows)
            df_meta_tags = pd.DataFrame(metas)
            df_inline_json = pd.DataFrame(inline_json_payloads)
            df_dom_map = pd.DataFrame(dom_map_like)

            # Mine network JSON for geo and then build df_map
            if not df_network.empty:
                for idx, row in df_network.iterrows():
                    try:
                        js = row.get("json")
                        if not isinstance(js, str):
                            continue
                        obj = json.loads(js)
                        geo_rows = recursively_find_geo(obj, path=f"network[{idx}] {row.get('url','')}")
                        for r in geo_rows:
                            r["source"] = row.get("url", "network")
                        map_rows.extend(geo_rows)
                    except Exception:
                        continue
            df_map = pd.DataFrame(map_rows)

            # Write to Excel
            with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
                df_meta.to_excel(writer, sheet_name="Overview", index=False)
                if not df_meta_tags.empty:
                    df_meta_tags.to_excel(writer, sheet_name="Meta", index=False)
                if not df_headings.empty:
                    df_headings.to_excel(writer, sheet_name="Headings", index=False)
                if not df_sections.empty:
                    df_sections.to_excel(writer, sheet_name="Sections", index=False)
                if not df_tables.empty:
                    df_tables.to_excel(writer, sheet_name="Tables", index=False)
                if not df_links.empty:
                    df_links.to_excel(writer, sheet_name="Links", index=False)
                if not df_images.empty:
                    df_images.to_excel(writer, sheet_name="Images", index=False)
                if not df_popups.empty:
                    df_popups.to_excel(writer, sheet_name="Popups", index=False)
                if not df_network.empty:
                    df_network.to_excel(writer, sheet_name="NetworkJSON", index=False)
                if not df_inline_json.empty:
                    df_inline_json.to_excel(writer, sheet_name="InlineJSON", index=False)
                if not df_dom_map.empty:
                    df_dom_map.to_excel(writer, sheet_name="DomMap", index=False)
                if not df_map.empty:
                    df_map.to_excel(writer, sheet_name="MapData", index=False)
                if not df_raw_text.empty:
                    df_raw_text.to_excel(writer, sheet_name="RawText", index=False)

            browser.close()
            return True, out_xlsx
    except Exception as exc:
        meta_info.update({"error": str(exc), "traceback": traceback.format_exc()})
        try:
            df_meta = pd.DataFrame([{**meta_info}])
            with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
                df_meta.to_excel(writer, sheet_name="Overview", index=False)
        except Exception:
            pass
        return False, str(exc)


def main(argv: List[str]) -> int:
    url = TARGET_URL_DEFAULT
    out_xlsx = OUTPUT_XLSX_DEFAULT
    if len(argv) > 1 and argv[1]:
        url = argv[1]
    if len(argv) > 2 and argv[2]:
        out_xlsx = argv[2]

    ok, info = run_scrape(url, out_xlsx)
    if ok:
        print(f"OK: Wrote Excel to {info}")
        return 0
    else:
        print(f"ERROR: {info}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))