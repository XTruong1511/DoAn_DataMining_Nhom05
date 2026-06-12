import csv
import os
import re
import time
import random
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import requests
from bs4 import BeautifulSoup


START_URL = "https://topdev.vn/jobs/search?page=1"
SOURCE = "TopDev"
BASE_URL = "https://topdev.vn"
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

CSV_FIELDS = [
    "job_title",
    "salary_min",
    "salarry_max",  # giữ đúng typo bạn yêu cầu
    "location",
    "experience",
    "job_description",
    "qualifications",
    "benefit",
    "job_location",
    "company",
    "size",
    "industry",
    "level",
    "working form",
    "salary_raw",
    "crawl_date",
    "source_url",
    "source",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://topdev.vn/jobs/search?page=1",
}


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_multiline_text(node) -> str:
    if not node:
        return ""

    for br in node.find_all("br"):
        br.replace_with("\n")

    parts = []

    for tag in node.find_all(["p", "li", "div"], recursive=True):
        text = clean_text(tag.get_text(" ", strip=True))
        if text:
            parts.append(text)

    if not parts:
        return clean_text(node.get_text(" ", strip=True))

    result = []
    seen = set()

    for item in parts:
        if item not in seen:
            result.append(item)
            seen.add(item)

    return "\n".join(result)


def build_page_url(url: str, page: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["page"] = [str(page)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def normalize_topdev_url(url: str) -> str:
    full_url = urljoin(BASE_URL, url)
    parsed = urlparse(full_url)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        "",
        ""
    ))


def get_soup_browser(page, url: str, timeout_ms: int = 120_000) -> BeautifulSoup:
    """
    Dùng browser thật để load TopDev, tránh lỗi TLS của requests/curl.
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(2500)

        html = page.content()
        return BeautifulSoup(html, "html.parser")

    except PlaywrightTimeoutError as e:
        raise TimeoutError(f"Playwright timeout khi tải: {url}") from e
def normalize_salary_number(num_text: str) -> int:
    """
    "40.000.000" -> 40000000
    "15" -> 15
    "1,500" -> 1500 nếu dạng thousands
    """
    num_text = num_text.strip()

    if re.search(r"[.,]\d{3}([.,]\d{3})*$", num_text):
        num_text = num_text.replace(".", "").replace(",", "")
        return int(num_text)

    num_text = num_text.replace(",", ".")
    return int(float(num_text))


def parse_salary_to_number(salary_raw: str) -> tuple[str, str]:
    if not salary_raw:
        return "", ""

    text = salary_raw.lower()
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if any(x in text for x in ["negotiable", "thoả thuận", "thỏa thuận", "cạnh tranh"]):
        return "", ""

    multiplier = 1

    if "triệu" in text or "trieu" in text:
        multiplier = 1_000_000
    elif "nghìn" in text or "ngàn" in text or re.search(r"\bk\b", text):
        multiplier = 1_000

    nums = re.findall(r"\d[\d.,]*", text)
    values = []

    for n in nums:
        try:
            values.append(normalize_salary_number(n) * multiplier)
        except Exception:
            pass

    if not values:
        return "", ""

    if len(values) >= 2:
        return str(values[0]), str(values[1])

    only = values[0]

    if any(x in text for x in ["up to", "upto", "lên đến", "tới", "đến"]):
        return "", str(only)

    if any(x in text for x in ["from", "từ", "trên"]):
        return str(only), ""

    return str(only), str(only)


def find_salary_text(node) -> str:
    if not node:
        return ""

    candidates = []

    for tag in node.find_all(["span", "div", "p"], recursive=True):
        text = clean_text(tag.get_text(" ", strip=True))

        if not text:
            continue

        lower = text.lower()

        if "negotiable" in lower:
            candidates.append(text)

        if "vnd" in lower or "usd" in lower or "triệu" in lower or "trieu" in lower:
            if re.search(r"\d", text):
                candidates.append(text)

    if candidates:
        candidates.sort(key=len)
        return candidates[0]

    return ""


def looks_like_detail_url(href: str) -> bool:
    if not href:
        return False

    parsed = urlparse(urljoin(BASE_URL, href))
    path = parsed.path

    return path.startswith("/detail-jobs/")


def find_card_container(anchor):
    """
    Đi ngược lên vài cấp để tìm card job.
    """
    parent = anchor

    for _ in range(10):
        parent = parent.parent

        if not parent or not getattr(parent, "name", None):
            break

        text = clean_text(parent.get_text(" ", strip=True))
        class_text = " ".join(parent.get("class", [])) if parent.get("class") else ""

        if (
            parent.name in ["div", "article"]
            and len(text) > 50
            and (
                "Fulltime" in text
                or "Parttime" in text
                or "Negotiable" in text
                or "VND" in text
                or "USD" in text
                or "rounded-xl" in class_text
            )
        ):
            return parent

    return anchor.parent


def extract_working_form_from_card(card) -> str:
    """
    Chỉ lấy working form từ card danh sách TopDev.
    Tránh lấy nhầm cả cụm location + level + working form + experience.
    """
    if not card:
        return ""

    working_forms = {
        "fulltime": "Fulltime",
        "parttime": "Parttime",
        "remote": "Remote",
        "hybrid": "Hybrid",
        "freelance": "Freelance",
        "contract": "Contract",
        "internship": "Internship",
        "onsite": "Onsite",
    }

    # Ưu tiên tìm trong khu vực grid metadata của card
    grid_candidates = []

    for div in card.find_all("div"):
        class_text = " ".join(div.get("class", [])) if div.get("class") else ""
        if "grid" in class_text and "grid-cols" in class_text:
            grid_candidates.append(div)

    # Nếu tìm được grid, chỉ lấy span con trực tiếp trong grid
    for grid in grid_candidates:
        for span in grid.find_all("span", recursive=False):
            text = clean_text(span.get_text(" ", strip=True))
            lower = text.lower()

            if lower in working_forms:
                return working_forms[lower]

            # Trường hợp text kiểu "Fulltime " hoặc có icon text lẫn vào
            for key, value in working_forms.items():
                if lower.strip() == key:
                    return value

    # Fallback: chỉ lấy những span ngắn, không lấy div cha
    for span in card.find_all("span"):
        text = clean_text(span.get_text(" ", strip=True))
        lower = text.lower()

        if not text:
            continue

        # Không nhận chuỗi dài kiểu "Hà Nội Junior Middle Fulltime 1 năm"
        if len(text) > 30:
            continue

        if lower in working_forms:
            return working_forms[lower]

    return ""
def extract_job_cards_from_list_page(soup: BeautifulSoup, page_url: str) -> dict[str, dict]:
    jobs = {}

    for a in soup.select('a[href*="/detail-jobs/"]'):
        href = a.get("href", "").strip()

        if not looks_like_detail_url(href):
            continue

        title_text = clean_text(a.get_text(" ", strip=True))

        if not title_text or title_text.lower() in ["apply now", "ứng tuyển ngay"]:
            continue

        detail_url = normalize_topdev_url(href)
        card = find_card_container(a)

        working_form = extract_working_form_from_card(card)

        if detail_url not in jobs:
            jobs[detail_url] = {
                "source_url": detail_url,
                "working form": working_form,
            }

    return jobs


def extract_prose_blocks(soup: BeautifulSoup) -> list[str]:
    blocks = []

    for div in soup.find_all("div"):
        class_text = " ".join(div.get("class", [])) if div.get("class") else ""

        if "prose-ul" not in class_text:
            continue

        text = clean_multiline_text(div)

        if text and text not in blocks:
            blocks.append(text)

    return blocks


def extract_section_by_heading(soup: BeautifulSoup, heading_keywords: list[str]) -> str:
    keywords = [x.lower() for x in heading_keywords]

    for heading in soup.find_all(["h2", "h3", "h4", "div", "span"]):
        heading_text = clean_text(heading.get_text(" ", strip=True)).lower()

        if len(heading_text) > 120:
            continue

        if not any(k in heading_text for k in keywords):
            continue

        parent = heading.find_parent()

        if parent:
            content = parent.find("div", class_=lambda c: c and "prose-ul" in c)
            if content:
                return clean_multiline_text(content)

        next_content = heading.find_next("div", class_=lambda c: c and "prose-ul" in c)
        if next_content:
            return clean_multiline_text(next_content)

    return ""


def extract_job_location(soup: BeautifulSoup) -> str:
    value = extract_labeled_value(
        soup,
        labels=["Địa điểm làm việc", "Working location", "Work location"],
        max_lookahead=4,
        max_value_len=250,
    )

    if value:
        return value

    # Fallback: lấy nguyên dòng có chứa label
    lines = get_visible_lines(soup)

    for line in lines:
        lower = line.lower()

        if "địa điểm làm việc" in lower:
            return line

        if "working location" in lower or "work location" in lower:
            return line

    return ""


def extract_company_name_from_detail(soup: BeautifulSoup) -> str:
    company_node = soup.select_one('a[href*="/companies/"]')
    if company_node:
        text = clean_text(company_node.get_text(" ", strip=True))
        if text:
            return text

    # fallback theo class text-brand-500, chọn text giống tên công ty
    for span in soup.find_all(["span", "a"]):
        text = clean_text(span.get_text(" ", strip=True))
        if not text:
            continue

        lower = text.lower()

        if any(x in lower for x in ["công ty", "company", "tnhh", "jsc", "corp", "ltd"]):
            if len(text) <= 120:
                return text

    return ""


def extract_labeled_value(soup: BeautifulSoup, labels: list[str]) -> str:
    labels_lower = [label.lower() for label in labels]

    lines = [clean_text(x) for x in soup.get_text("\n", strip=True).splitlines()]
    lines = [x for x in lines if x]

    for idx, line in enumerate(lines):
        lower = line.lower()

        if any(label in lower for label in labels_lower):
            # Trường hợp "Industry Phần Mềm"
            for label in labels:
                pattern = re.compile(re.escape(label), re.IGNORECASE)
                candidate = clean_text(pattern.sub("", line).strip(" :-"))
                if candidate and candidate.lower() != label.lower() and len(candidate) < 80:
                    return candidate

            # Trường hợp label nằm riêng một dòng, value nằm dòng sau
            for j in range(idx + 1, min(idx + 5, len(lines))):
                candidate = lines[j]
                candidate_lower = candidate.lower()

                if candidate_lower in labels_lower:
                    continue

                if len(candidate) <= 80:
                    return candidate

    return ""


def extract_size_fallback(soup: BeautifulSoup) -> str:
    text = clean_text(soup.get_text(" ", strip=True))

    m = re.search(
        r"\b\d[\d.,]*\s*-\s*\d[\d.,]*\s*(?:Employees|employees|nhân viên)\b",
        text,
        flags=re.IGNORECASE,
    )

    if m:
        return clean_text(m.group(0))

    return ""




def extract_title_from_detail(soup: BeautifulSoup, fallback: str = "") -> str:
    # Detail page TopDev thường có a[href="/detail-jobs/..."] là title
    for a in soup.select('a[href*="/detail-jobs/"]'):
        text = clean_text(a.get_text(" ", strip=True))
        if text and text.lower() not in ["apply now", "ứng tuyển ngay"]:
            if len(text) > 5:
                return text

    h1 = soup.find("h1")
    if h1:
        text = clean_text(h1.get_text(" ", strip=True))
        if text:
            return text

    return fallback
def get_node_class_text(node) -> str:
    if not node:
        return ""
    return " ".join(node.get("class", [])) if node.get("class") else ""


def get_lines_from_node(node) -> list[str]:
    if not node:
        return []

    lines = []
    seen = set()

    for line in node.get_text("\n", strip=True).splitlines():
        line = clean_text(line)

        if not line:
            continue

        if line not in seen:
            lines.append(line)
            seen.add(line)

    return lines


def find_detail_title_node(soup: BeautifulSoup, current_url: str = ""):
    """
    Ưu tiên lấy title anchor trùng URL detail hiện tại.
    Tránh lấy nhầm title ở related jobs.
    """
    current_path = urlparse(current_url).path if current_url else ""

    candidates = []

    for a in soup.select('a[href*="/detail-jobs/"]'):
        text = clean_text(a.get_text(" ", strip=True))
        href = a.get("href", "")

        if not text:
            continue

        if text.lower() in ["apply now", "ứng tuyển ngay"]:
            continue

        href_path = urlparse(urljoin(BASE_URL, href)).path

        if current_path and href_path == current_path:
            return a

        candidates.append(a)

    if candidates:
        return candidates[0]

    return soup.find("h1")


def is_salary_header_text(text: str) -> bool:
    """
    Chỉ dùng để nhận diện salary trong vùng header, không quét toàn trang.
    """
    if not text:
        return False

    text = clean_text(text)
    lower = text.lower()

    if lower in ["negotiable", "thỏa thuận", "thoả thuận", "login to view salary"]:
        return True

    if len(text) > 120:
        return False

    if re.search(r"\d", text) and any(x in lower for x in ["vnd", "usd", "triệu", "trieu"]):
        return True

    return False


def find_detail_header_container(soup: BeautifulSoup, current_url: str = ""):
    """
    Tìm vùng header chứa title + salary + metadata.
    Không lấy toàn trang để tránh dính benefit/related jobs.
    """
    title_node = find_detail_title_node(soup, current_url)

    if not title_node:
        return None

    title_text = clean_text(title_node.get_text(" ", strip=True))

    node = title_node

    for _ in range(12):
        if not node:
            break

        lines = get_lines_from_node(node)

        if not lines:
            node = node.parent
            continue

        has_title = title_text in lines or title_text in clean_text(node.get_text(" ", strip=True))
        has_salary = any(is_salary_header_text(line) for line in lines)

        # Header thường có title + salary + location + level + experience
        if has_title and has_salary and len(lines) >= 4:
            return node

        node = node.parent

    return title_node.parent


def extract_detail_header_fields(soup: BeautifulSoup, current_url: str = "") -> dict:
    """
    Lấy các field header theo cấu trúc/thứ tự DOM:
    title
    salary
    location
    level
    experience

    working form vẫn lấy từ card danh sách.
    """
    title_node = find_detail_title_node(soup, current_url)
    header = find_detail_header_container(soup, current_url)

    title = clean_text(title_node.get_text(" ", strip=True)) if title_node else ""

    lines = get_lines_from_node(header)

    salary_raw = ""
    salary_index = -1

    for i, line in enumerate(lines):
        if is_salary_header_text(line):
            salary_raw = line
            salary_index = i
            break

    meta_lines = []

    if salary_index >= 0:
        for line in lines[salary_index + 1:]:
            lower = line.lower()

            if not line:
                continue

            if line == title or line == salary_raw:
                continue

            if lower in ["apply now", "save this job", "view company", "favorite"]:
                continue

            if lower in ["your role", "responsibilities", "mô tả công việc", "your skills", "benefits"]:
                break

            if len(line) <= 140:
                meta_lines.append(line)

    # Theo header TopDev: location, level, experience
    location = meta_lines[0] if len(meta_lines) >= 1 else ""
    level = meta_lines[1] if len(meta_lines) >= 2 else ""
    experience = meta_lines[2] if len(meta_lines) >= 3 else ""

    return {
        "job_title": title,
        "salary_raw": salary_raw,
        "location": location,
        "level": level,
        "experience": experience,
    }
def get_visible_lines(soup: BeautifulSoup) -> list[str]:
    """
    Tách text trang thành từng dòng sạch.
    Hữu ích khi HTML bị chia nhiều div/span.
    """
    lines = []

    for line in soup.get_text("\n", strip=True).splitlines():
        line = clean_text(line)
        if line:
            lines.append(line)

    return lines


def is_noise_line(text: str) -> bool:
    lower = text.lower().strip()

    noise_values = {
        "apply now",
        "save this job",
        "view company",
        "view more jobs",
        "other jobs at this company",
        "more jobs for you",
        "hot jobs",
        "jobs",
        "company",
        "tools",
        "blog",
        "premium recruitment zone",
    }

    return lower in noise_values


def extract_labeled_value_from_lines(
    soup: BeautifulSoup,
    labels: list[str],
    max_lookahead: int = 6,
    max_value_len: int = 160,
) -> str:
    """
    Lấy value dựa trên text label.
    Ví dụ:
    Industry
    Phần Mềm

    hoặc:
    Industry Phần Mềm
    """
    labels_lower = [x.lower() for x in labels]
    lines = get_visible_lines(soup)

    for idx, line in enumerate(lines):
        lower = line.lower()

        matched_label = None
        for label in labels:
            label_lower = label.lower()
            if lower == label_lower or lower.startswith(label_lower + " ") or lower.startswith(label_lower + ":"):
                matched_label = label
                break

        if not matched_label:
            continue

        # Case 1: label và value cùng dòng
        # Ví dụ: "Industry Phần Mềm" hoặc "Industry: Phần Mềm"
        same_line_value = re.sub(
            rf"^{re.escape(matched_label)}\s*:?\s*",
            "",
            line,
            flags=re.IGNORECASE,
        ).strip()

        if (
            same_line_value
            and same_line_value.lower() != matched_label.lower()
            and len(same_line_value) <= max_value_len
            and not is_noise_line(same_line_value)
        ):
            return same_line_value

        # Case 2: value nằm ở vài dòng tiếp theo
        for j in range(idx + 1, min(idx + 1 + max_lookahead, len(lines))):
            candidate = clean_text(lines[j])
            candidate_lower = candidate.lower()

            if not candidate:
                continue

            if is_noise_line(candidate):
                continue

            # Gặp label khác thì dừng
            if any(candidate_lower == lb for lb in labels_lower):
                continue

            # Tránh lấy nhầm đoạn mô tả dài
            if len(candidate) <= max_value_len:
                return candidate

    return ""


def extract_value_near_label_dom(
    soup: BeautifulSoup,
    labels: list[str],
    max_value_len: int = 160,
) -> str:
    """
    Tìm label trong DOM, rồi lấy text ở sibling / parent gần đó.
    Mạnh hơn get_text toàn trang trong một số layout.
    """
    labels_lower = [x.lower() for x in labels]

    for node in soup.find_all(["div", "span", "p", "label"]):
        node_text = clean_text(node.get_text(" ", strip=True))
        node_lower = node_text.lower()

        if not node_text:
            continue

        is_label = False
        matched_label = ""

        for label in labels:
            label_lower = label.lower()

            if node_lower == label_lower or node_lower.startswith(label_lower + ":"):
                is_label = True
                matched_label = label
                break

        if not is_label:
            continue

        # 1. Value cùng node
        same_node_value = re.sub(
            rf"^{re.escape(matched_label)}\s*:?\s*",
            "",
            node_text,
            flags=re.IGNORECASE,
        ).strip()

        if (
            same_node_value
            and same_node_value.lower() not in labels_lower
            and len(same_node_value) <= max_value_len
            and not is_noise_line(same_node_value)
        ):
            return same_node_value

        # 2. Value ở sibling kế tiếp
        sibling = node.find_next_sibling()
        for _ in range(4):
            if not sibling:
                break

            candidate = clean_text(sibling.get_text(" ", strip=True))

            if (
                candidate
                and candidate.lower() not in labels_lower
                and len(candidate) <= max_value_len
                and not is_noise_line(candidate)
            ):
                return candidate

            sibling = sibling.find_next_sibling()

        # 3. Value ở parent
        parent = node.find_parent()
        if parent:
            parent_text = clean_text(parent.get_text(" ", strip=True))

            value = re.sub(
                rf"{re.escape(matched_label)}\s*:?\s*",
                "",
                parent_text,
                count=1,
                flags=re.IGNORECASE,
            ).strip()

            if (
                value
                and value.lower() not in labels_lower
                and len(value) <= max_value_len
                and not is_noise_line(value)
            ):
                return value

    return ""


def extract_labeled_value(
    soup: BeautifulSoup,
    labels: list[str],
    max_lookahead: int = 6,
    max_value_len: int = 160,
) -> str:
    """
    Hàm tổng hợp: thử DOM trước, rồi thử text lines.
    Không đoán bằng danh sách ngành cố định.
    """
    value = extract_value_near_label_dom(
        soup,
        labels=labels,
        max_value_len=max_value_len,
    )

    if value:
        return value

    return extract_labeled_value_from_lines(
        soup,
        labels=labels,
        max_lookahead=max_lookahead,
        max_value_len=max_value_len,
    )


def extract_company_size(soup: BeautifulSoup) -> str:
    value = extract_labeled_value(
        soup,
        labels=["Size", "Company size", "Quy mô", "Quy mô công ty"],
        max_value_len=80,
    )

    if value:
        return value

    # Fallback theo pattern, không phải danh sách đoán.
    text = clean_text(soup.get_text(" ", strip=True))

    patterns = [
        r"\b\d[\d.,]*\s*-\s*\d[\d.,]*\s*(?:Employees|employees|nhân viên)\b",
        r"\b\d[\d.,]*\+?\s*(?:Employees|employees|nhân viên)\b",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return clean_text(m.group(0))

    return ""


def extract_company_industry(soup: BeautifulSoup) -> str:
    """
    Lấy industry theo label thật trên trang.
    Không dùng common_industries để tránh mất ngành lạ.
    """
    return extract_labeled_value(
        soup,
        labels=["Industry", "Lĩnh vực", "Field", "Business field", "Ngành nghề"],
        max_value_len=100,
    )

def crawl_job_detail(page, url: str, card_info: dict | None = None) -> dict:
    card_info = card_info or {}
    soup = get_soup_browser(page, url)

    prose_blocks = extract_prose_blocks(soup)

    job_description = extract_section_by_heading(soup, [
        "your role",
        "responsibilities",
        "mô tả công việc",
        "trách nhiệm",
    ])

    qualifications = extract_section_by_heading(soup, [
        "your skills",
        "qualifications",
        "requirements",
        "yêu cầu",
        "kỹ năng",
    ])

    benefit = extract_section_by_heading(soup, [
        "benefits",
        "quyền lợi",
        "phúc lợi",
        "why you'll love",
        "why you will love",
    ])

    # Fallback theo thứ tự block prose-ul:
    # 0: mô tả, 1: yêu cầu, 2: quyền lợi
    if not job_description and len(prose_blocks) >= 1:
        job_description = prose_blocks[0]

    if not qualifications and len(prose_blocks) >= 2:
        qualifications = prose_blocks[1]

    if not benefit and len(prose_blocks) >= 3:
        benefit = prose_blocks[2]

    header_fields = extract_detail_header_fields(soup, url)

    salary_raw = header_fields.get("salary_raw", "")
    salary_min, salary_max = parse_salary_to_number(salary_raw)

    company = extract_company_name_from_detail(soup)
    size = extract_company_size(soup)
    industry = extract_company_industry(soup)

    data = {
        "job_title": header_fields.get("job_title", ""),
        "salary_min": salary_min,
        "salarry_max": salary_max,
        "location": header_fields.get("location", ""),
        "experience": header_fields.get("experience", ""),
        "job_description": job_description,
        "qualifications": qualifications,
        "benefit": benefit,
        "job_location": extract_job_location(soup),
        "company": company,
        "size": size,
        "industry": industry,
        "level": header_fields.get("level", ""),
        "working form": card_info.get("working form", ""),
        "salary_raw": salary_raw,
        "crawl_date": datetime.now().strftime("%Y-%m-%d"),
        "source_url": url,
        "source": SOURCE,
    }

    return data

def load_crawled_urls(output_csv: str) -> set[str]:
    if not os.path.exists(output_csv):
        return set()

    crawled = set()

    try:
        with open(output_csv, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("source_url", "")
                if url:
                    crawled.add(url)
    except Exception:
        pass

    return crawled


def crawl_topdev(
    start_url: str,
    output_csv: str,
    max_pages: int,
    delay_min: float,
    delay_max: float,
    resume: bool,
):
    all_jobs: dict[str, dict] = {}

    print("Bắt đầu lấy link job từ danh sách TopDev bằng browser...")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="topdev_browser_profile",
            executable_path=BRAVE_PATH,
            headless=False,
            locale="vi-VN",
            user_agent=HEADERS["User-Agent"],
            viewport={"width": 1366, "height": 768},
        )

        page = context.pages[0] if context.pages else context.new_page()

        for page_num in range(1, max_pages + 1):
            page_url = build_page_url(start_url, page_num)
            print(f"[LIST] Page {page_num}/{max_pages}: {page_url}")

            try:
                soup = get_soup_browser(page, page_url)
                page_jobs = extract_job_cards_from_list_page(soup, page_url)

            except KeyboardInterrupt:
                print("\nBạn đã dừng khi đang lấy danh sách link.")
                break

            except Exception as e:
                print(f"  Lỗi lấy page {page_num}: {e}")

                if page_num == 1:
                    print("  Page 1 không tải được, dừng để kiểm tra browser.")
                    break

                continue

            new_count = 0

            for url, info in page_jobs.items():
                if url not in all_jobs:
                    all_jobs[url] = info
                    new_count += 1

            print(f"  Tìm thấy {len(page_jobs)} job, mới {new_count} job.")

            if len(page_jobs) == 0 and page_num > 1:
                print("  Không thấy job nào ở page này, dừng pagination.")
                break

            time.sleep(random.uniform(delay_min, delay_max))

        print(f"\nTổng số job detail sẽ crawl: {len(all_jobs)}")

        crawled_urls = load_crawled_urls(output_csv) if resume else set()

        if resume and crawled_urls:
            print(f"Resume mode: đã có {len(crawled_urls)} URL trong CSV, sẽ bỏ qua các URL này.")

        file_exists = os.path.exists(output_csv)
        write_header = not (resume and file_exists)
        mode = "a" if resume and file_exists else "w"

        failed_urls = []
        success_count = 0
        skipped_count = 0

        with open(output_csv, mode, encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=CSV_FIELDS,
                quoting=csv.QUOTE_ALL,
            )

            if write_header:
                writer.writeheader()

            job_items = list(all_jobs.items())

            for idx, (job_url, card_info) in enumerate(job_items, start=1):
                if resume and job_url in crawled_urls:
                    skipped_count += 1
                    continue

                print(f"[DETAIL] {idx}/{len(job_items)}: {job_url}")

                try:
                    row = crawl_job_detail(page, job_url, card_info=card_info)

                    safe_row = {
                        field: row.get(field, "")
                        for field in CSV_FIELDS
                    }

                    writer.writerow(safe_row)
                    f.flush()

                    success_count += 1
                    print(f"  OK - đã lưu dòng mới {success_count}")

                except KeyboardInterrupt:
                    print("\nBạn đã dừng chương trình.")
                    print("Các dòng đã crawl trước đó vẫn được lưu trong CSV.")
                    break

                except Exception as e:
                    print(f"  Lỗi crawl detail: {e}")
                    failed_urls.append(job_url)

                time.sleep(random.uniform(delay_min, delay_max))

        if failed_urls:
            with open("failed_topdev_urls.txt", "w", encoding="utf-8") as f:
                for url in failed_urls:
                    f.write(url + "\n")

            print(f"\nĐã lưu {len(failed_urls)} URL lỗi vào failed_topdev_urls.txt")

        context.close()


    print("\nHoàn tất.")
    print(f"  Lưu mới: {success_count}")
    print(f"  Bỏ qua do đã crawl: {skipped_count}")
    print(f"  File CSV: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl TopDev jobs to CSV")
    parser.add_argument("--url", default=START_URL, help="URL trang danh sách TopDev")
    parser.add_argument("--output", default="topdev_it_jobs.csv", help="Tên file CSV output")
    parser.add_argument("--max-pages", type=int, default=261, help="Số trang danh sách muốn crawl")
    parser.add_argument("--delay-min", type=float, default=4.0, help="Delay thấp nhất giữa request")
    parser.add_argument("--delay-max", type=float, default=8.0, help="Delay cao nhất giữa request")
    parser.add_argument("--resume", action="store_true", help="Bỏ qua URL đã có trong CSV output")

    args = parser.parse_args()

    crawl_topdev(
        start_url=args.url,
        output_csv=args.output,
        max_pages=args.max_pages,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        resume=args.resume,
    )