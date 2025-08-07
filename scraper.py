import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Any, Optional


def _get_text(elem, default: str = "N/A") -> str:
    """Safely extract text from a BeautifulSoup element."""
    try:
        if elem is None:
            return default
        return elem.get_text(strip=True)
    except Exception:
        return default


def get_soup(url: str) -> BeautifulSoup:
    """Fetch the HTML content of a URL and return a BeautifulSoup object."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


# ---------------------------------------------------------------------------
# 1. Scan Information & Rank Summary
# ---------------------------------------------------------------------------

def scrape_ozet_bilgiler(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract summary information and rank summary as a flat dictionary."""

    results: Dict[str, Any] = {}

    # --- Scan Information Table ------------------------------------------------
    scan_header = soup.find("h4", string=re.compile(r"^\s*Scan Information\s*$", re.I))
    if scan_header:
        scan_table = scan_header.find_next("table")
        if scan_table:
            results["İşletme Adı"] = _get_text(scan_table.select_one("span.bizname"))
            results["Adres"] = _get_text(scan_table.select_one("span.center-block"))
            results["Yorum Sayısı"] = _get_text(scan_table.select_one("div.rating-container + span"))

            # Keyword & language
            kw_td = scan_table.find("td", string=re.compile(r"Keyword", re.I))
            kw_val_td = kw_td.find_next_sibling("td") if kw_td else None
            results["Anahtar Kelime ve Dil"] = _get_text(kw_val_td)

            # Date
            date_td = scan_table.find("td", class_=re.compile(r"cnv_dt_lcl", re.I))
            results["Tarih"] = _get_text(date_td)

    # --- Rank Summary Table ----------------------------------------------------
    rank_header = soup.find("h4", string=re.compile(r"^\s*Rank Summary\s*$", re.I))
    if rank_header:
        rank_table = rank_header.find_next("table")
        if rank_table:
            for tr in rank_table.select("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    key = _get_text(tds[0], default="")
                    value = _get_text(tds[1])
                    if key:
                        results[key] = value
    return results


# ---------------------------------------------------------------------------
# 2. Competitors (Rakipler)
# ---------------------------------------------------------------------------

def scrape_rakipler(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract competitor information from the competitors table."""

    competitors: List[Dict[str, Any]] = []
    rows = soup.select("table#tbl_comp_rank tbody tr")

    for row in rows:
        comp: Dict[str, Any] = {
            "İsim": _get_text(row.select_one("a.ext")),
            "Puan/Yorum": _get_text(row.select_one("div.rating-container + span")),
        }

        # Address (look for span containing map marker icon)
        addr_span = None
        map_icon = row.select_one("i.fa-map-marker")
        if map_icon:
            addr_span = map_icon.find_parent("span")
        comp["Adres"] = _get_text(addr_span)

        # Categories
        cat_p = row.find("p", string=re.compile(r"Categories:", re.I))
        comp["Kategoriler"] = _get_text(cat_p)

        # Website
        website_link: Optional[str] = None
        globe_icon = row.select_one("i.fa-globe")
        if globe_icon:
            parent_span = globe_icon.find_parent("span")
            if parent_span:
                a_tag = parent_span.find("a", href=True)
                if a_tag:
                    website_link = a_tag["href"]
        comp["Web Sitesi"] = website_link or "N/A"

        # Photo count
        photo_span = None
        photo_icon = row.select_one("i.fa-photo")
        if photo_icon:
            photo_span = photo_icon.find_parent("span")
        comp["Fotoğraf Sayısı"] = _get_text(photo_span)

        # Ownership status
        claim_span = row.find("span", string=re.compile(r"(Claimed|Un\s*Claimed)", re.I))
        comp["Sahiplenme Durumu"] = _get_text(claim_span)

        # Location count
        comp["Bulunduğu Konum Sayısı"] = _get_text(row.select_one("td.text-center > h5"))

        # Average Ranking (AR)
        comp["Ortalama Sıralama"] = _get_text(row.select_one("span.dotlg2"))

        competitors.append(comp)

    return competitors


# ---------------------------------------------------------------------------
# 3. Sponsored Listings (Sponsorlu Listeler)
# ---------------------------------------------------------------------------

def scrape_sponsorlu_listeler(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract sponsored listings data."""

    listings: List[Dict[str, Any]] = []
    rows = soup.select("table#tbl_ads_rank tbody tr")

    for row in rows:
        tds = row.find_all("td")
        isim = _get_text(row.select_one("a.ext"))
        rating = _get_text(row.select_one("div.rating-container + span"))
        gorulme_sayisi = _get_text(tds[-1] if tds else None)

        listings.append({
            "İsim": isim,
            "Puan/Yorum": rating,
            "Görülme Sayısı": gorulme_sayisi,
        })

    return listings


# ---------------------------------------------------------------------------
# 4. Detailed Results (Detaylı Sonuçlar)
# ---------------------------------------------------------------------------

def scrape_detayli_sonuclar(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract detailed results from the modal results body."""

    detaylar: List[Dict[str, Any]] = []

    container = soup.select_one("div#resultModal div.results_body")
    if not container:
        return detaylar

    panels = container.select("div.bg-light.panel-body")
    for panel in panels:
        rank = _get_text(panel.select_one("span.dot"))
        name = _get_text(panel.select_one("h5"))
        rating_span = panel.select_one("div.rating-container + span")
        rating = _get_text(rating_span)

        # Address is typically the next div after the rating span
        address_div = rating_span.find_next("div") if rating_span else None
        address = _get_text(address_div)

        detaylar.append({
            "Sıra": rank,
            "İsim": name,
            "Puan/Yorum": rating,
            "Adres": address,
        })

    return detaylar


# ---------------------------------------------------------------------------
# 5. Map Data (Harita Verileri)
# ---------------------------------------------------------------------------

def _safe_json_loads(text: str):
    """Attempt to load JSON, falling back to a relaxed eval when needed."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import ast
            # Replace JavaScript boolean / null with Python equivalents
            text = re.sub(r"\btrue\b", "true", text, flags=re.I)
            text = re.sub(r"\bfalse\b", "false", text, flags=re.I)
            text = re.sub(r"\bnull\b", "None", text, flags=re.I)
            return ast.literal_eval(text)
        except Exception:
            return []


def scrape_harita_verileri(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract map pin data from script tag."""

    pins: List[Dict[str, Any]] = []

    for script in soup.find_all("script"):
        script_text = script.string or ""
        if "var pinz" in script_text:
            match = re.search(r"var\s+pinz\s*=\s*(\[.*?\]);", script_text, re.DOTALL)
            if match:
                raw_json = match.group(1)
                data = _safe_json_loads(raw_json)
                for obj in data:
                    if not isinstance(obj, dict):
                        continue
                    pins.append({
                        "lat": obj.get("lat") or obj.get("latitude"),
                        "lon": obj.get("lon") or obj.get("lng") or obj.get("longitude"),
                        "label": obj.get("lable") or obj.get("label"),
                        "title": obj.get("title"),
                    })
            break  # Stop after first match
    return pins


# ---------------------------------------------------------------------------
# Example Usage (for manual testing)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    URL = "https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb"
    soup = get_soup(URL)

    print("--- Özet Bilgiler ---")
    print(json.dumps(scrape_ozet_bilgiler(soup), ensure_ascii=False, indent=2))

    print("\n--- Rakipler ---")
    print(json.dumps(scrape_rakipler(soup), ensure_ascii=False, indent=2))

    print("\n--- Sponsorlu Listeler ---")
    print(json.dumps(scrape_sponsorlu_listeler(soup), ensure_ascii=False, indent=2))

    print("\n--- Detaylı Sonuçlar ---")
    print(json.dumps(scrape_detayli_sonuclar(soup), ensure_ascii=False, indent=2))

    print("\n--- Harita Verileri ---")
    print(json.dumps(scrape_harita_verileri(soup), ensure_ascii=False, indent=2))