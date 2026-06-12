import csv
import re
import time
import random
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
    

import requests
from bs4 import BeautifulSoup


START_URL = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257?type_keyword=1&sba=1&saturday_status=0&ta_source=search_noKWnJF"

SOURCE = "TopCV"

CSV_FIELDS = [
    "job_title",
    "salary_min",
    "salarry_max",  # giữ đúng tên field bạn yêu cầu, dù có typo
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
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Referer": "https://www.topcv.vn/",
}

def normalize_job_url(url: str) -> str:
    """
    Bỏ query tracking như ta_source, u_sr_id.
    Giữ lại URL detail sạch.
    """
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        "",
        ""
    )
)

def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_multiline_text(node) -> str:
    """
    Giữ nội dung mô tả/yêu cầu/quyền lợi dễ đọc hơn get_text bình thường.
    """
    if not node:
        return ""

    for br in node.find_all("br"):
        br.replace_with("\n")

    parts = []

    for child in node.find_all(["p", "li", "div"], recursive=True):
        text = clean_text(child.get_text(" ", strip=True))
        if text:
            parts.append(text)

    # Nếu không bắt được p/li/div thì fallback
    if not parts:
        text = clean_text(node.get_text(" ", strip=True))
        return text

    # Deduplicate nhẹ vì div cha có thể chứa text của p/li con
    result = []
    seen = set()
    for item in parts:
        if item not in seen:
            result.append(item)
            seen.add(item)

    return "\n".join(result)


def get_soup(session: requests.Session, url: str, timeout: int = 25) -> BeautifulSoup:
    last_error = None

    for attempt in range(1, 4):
        try:
            resp = session.get(
                url,
                timeout=(8, timeout),
                headers={
                    "Referer": "https://www.topcv.vn/",
                }
            )

            if resp.status_code == 403:
                wait_time = 30 * attempt
                print(f"  Bị 403 Forbidden. Nghỉ {wait_time}s rồi thử lại lần {attempt}/3...")
                time.sleep(wait_time)
                last_error = requests.HTTPError(f"403 Forbidden: {url}")
                continue

            if resp.status_code == 429:
                wait_time = 60 * attempt
                print(f"  Bị 429 Too Many Requests. Nghỉ {wait_time}s rồi thử lại lần {attempt}/3...")
                time.sleep(wait_time)
                last_error = requests.HTTPError(f"429 Too Many Requests: {url}")
                continue

            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
        ) as e:
            last_error = e
            wait_time = 10 * attempt
            print(f"  Lỗi mạng/timeout: {e}. Nghỉ {wait_time}s rồi thử lại...")
            time.sleep(wait_time)

    raise last_error


def build_page_url(url: str, page: int) -> str:
    """
    TopCV thường dùng query page.
    Giữ nguyên query gốc, chỉ thêm/sửa page.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["page"] = [str(page)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def extract_job_links_from_list_page(soup: BeautifulSoup, base_url: str) -> list[str]:
    """
    Lấy link job detail từ trang danh sách.
    Có nhiều anchor trên TopCV nên phải lọc bớt link search/company/blog.
    """
    links = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if "topcv.vn" not in parsed.netloc:
            continue

        path = parsed.path

        # Link job detail TopCV thường có dạng /viec-lam/... hoặc /tim-viec-lam-...
        # Loại các link search/list/company/login/cv.
        bad_keywords = [
            "/tim-viec-lam-cong-nghe-thong-tin",
            "/cong-ty/",
            "/company/",
            "/blog/",
            "/mau-cv",
            "/cv/",
            "/login",
            "/viec-lam",
        ]

        # Ưu tiên link có /viec-lam/ hoặc có "-j" / ".html" thường gặp ở detail
        looks_like_job = (
            "/viec-lam/" in path
            or re.search(r"/tim-viec-lam-[^/]+-j\d+", path)
            or re.search(r"/viec-lam-[^/]+-j\d+", path)
        )

        if not looks_like_job:
            continue

        # Không lấy link category/search
        if "tim-viec-lam-cong-nghe-thong-tin-cr257" in full_url:
            continue

        links.add(normalize_job_url(full_url))

    return sorted(links)


def extract_info_section(soup: BeautifulSoup, label: str) -> str:
    """
    Lấy các field đầu trang như:
    - Mức lương
    - Địa điểm
    - Kinh nghiệm

    Dựa vào:
    div.job-detail__info--section-content-title
    div.job-detail__info--section-content-value
    """
    for section in soup.select(".job-detail__info--section-content"):
        title_node = section.select_one(".job-detail__info--section-content-title")
        value_node = section.select_one(".job-detail__info--section-content-value")

        title = clean_text(title_node.get_text(" ", strip=True)) if title_node else ""
        if label.lower() in title.lower():
            return clean_text(value_node.get_text(" ", strip=True)) if value_node else ""

    return ""


def extract_description_block_by_h3(soup: BeautifulSoup, h3_keyword: str) -> str:
    """
    Lấy nội dung các block:
    - Mô tả công việc
    - Yêu cầu ứng viên
    - Quyền lợi
    - Địa điểm làm việc

    Dựa vào h3 rồi lấy .job-description__item--content gần nhất.
    """
    h3_keyword_lower = h3_keyword.lower()

    for h3 in soup.find_all("h3"):
        h3_text = clean_text(h3.get_text(" ", strip=True)).lower()

        if h3_keyword_lower in h3_text:
            container = h3.find_parent()
            if container:
                content = container.select_one(".job-description__item--content")
                if content:
                    return clean_multiline_text(content)

            # Fallback: tìm sibling kế tiếp
            next_content = h3.find_next("div", class_="job-description__item--content")
            if next_content:
                return clean_multiline_text(next_content)

    return ""


def extract_company_value(soup: BeautifulSoup, label: str) -> str:
    """
    Lấy thông tin company sidebar:
    - Quy mô
    - Lĩnh vực

    Dựa vào .company-title chứa label và .company-value.
    """
    label_lower = label.lower()

    for item in soup.select(".job-detail__company--information-item, .company-field, .company-subdetail-label, div"):
        title_node = item.select_one(".company-title")
        value_node = item.select_one(".company-value")

        if not title_node or not value_node:
            continue

        title = clean_text(title_node.get_text(" ", strip=True)).lower()
        if label_lower in title:
            return clean_text(value_node.get_text(" ", strip=True))

    return ""


def extract_general_info_value(soup: BeautifulSoup, label: str) -> str:
    """
    Lấy thông tin dạng general info:
    - Cấp bậc
    - Hình thức làm việc

    TopCV có thể đổi class, nên dùng nhiều fallback.
    """
    label_lower = label.lower()

    possible_items = soup.select(
        ".box-general-group-info, "
        ".box-general-group-info-item, "
        ".box-general-group, "
        ".job-detail__info--section-content"
    )

    for item in possible_items:
        item_text = clean_text(item.get_text(" ", strip=True)).lower()
        if label_lower not in item_text:
            continue

        value_node = item.select_one(".box-general-group-info-value")
        if value_node:
            return clean_text(value_node.get_text(" ", strip=True))

        # Fallback: nếu có label + value cùng block
        text = clean_text(item.get_text(" ", strip=True))
        text = re.sub(label, "", text, flags=re.IGNORECASE).strip(" :-")
        if text:
            return text

    return ""


def extract_company_name(soup: BeautifulSoup) -> str:
    node = soup.select_one(".company-name-label a.name")
    if node:
        return clean_text(node.get_text(" ", strip=True))

    # Fallback
    node = soup.select_one(".job-detail__company--information a")
    if node:
        return clean_text(node.get_text(" ", strip=True))

    return ""


def extract_job_title(soup: BeautifulSoup) -> str:
    node = soup.select_one("h1.job-detail__info--title")
    if node:
        return clean_text(node.get_text(" ", strip=True))

    node = soup.find("h1")
    return clean_text(node.get_text(" ", strip=True)) if node else ""


def parse_salary_to_vnd(salary_raw: str) -> tuple[str, str]:
    """
    Parse salary_raw sang VND dạng số nguyên.

    Ví dụ:
    "12 - 17 triệu"        -> 12000000, 17000000
    "Tới 20 triệu"         -> "", 20000000
    "Trên 15 triệu"        -> 15000000, ""
    "Thoả thuận"           -> "", ""
    "Negotiable"           -> "", ""

    CSV xuất ra string để tránh lỗi format Excel.
    """
    if not salary_raw:
        return "", ""

    text = salary_raw.lower()
    text = text.replace(",", ".")
    text = re.sub(r"\s+", " ", text).strip()

    if any(x in text for x in ["thoả thuận", "thỏa thuận", "negotiable", "cạnh tranh"]):
        return "", ""

    multiplier = 1

    if "triệu" in text or "trieu" in text:
        multiplier = 1_000_000
    elif "nghìn" in text or "ngàn" in text or "k" in text:
        multiplier = 1_000
    elif "usd" in text or "$" in text:
        # Nếu muốn quy đổi USD sang VND, sửa tỷ giá ở đây.
        # Hiện tại giữ nguyên con số USD, không quy đổi.
        multiplier = 1

    nums = re.findall(r"\d+(?:\.\d+)?", text)
    values = [int(float(n) * multiplier) for n in nums]

    if not values:
        return "", ""

    # "12 - 17 triệu"
    if len(values) >= 2:
        return str(values[0]), str(values[1])

    only = values[0]

    # "Tới 20 triệu", "Lên đến 20 triệu", "Up to 20"
    if any(x in text for x in ["tới", "đến", "upto", "up to", "lên đến"]):
        return "", str(only)

    # "Trên 15 triệu", "Từ 15 triệu"
    if any(x in text for x in ["trên", "từ", "from"]):
        return str(only), ""

    return str(only), str(only)


def crawl_job_detail(session: requests.Session, url: str) -> dict:
    soup = get_soup(session, url)

    salary_raw = extract_info_section(soup, "Mức lương")
    salary_min, salary_max = parse_salary_to_vnd(salary_raw)

    data = {
        "job_title": extract_job_title(soup),
        "salary_min": salary_min,
        "salarry_max": salary_max,
        "location": extract_info_section(soup, "Địa điểm"),
        "experience": extract_info_section(soup, "Kinh nghiệm"),
        "job_description": extract_description_block_by_h3(soup, "Mô tả công việc"),
        "qualifications": extract_description_block_by_h3(soup, "Yêu cầu ứng viên"),
        "benefit": extract_description_block_by_h3(soup, "Quyền lợi"),
        "job_location": extract_description_block_by_h3(soup, "Địa điểm làm việc"),
        "company": extract_company_name(soup),
        "size": extract_company_value(soup, "Quy mô"),
        "industry": extract_company_value(soup, "Lĩnh vực"),
        "level": extract_general_info_value(soup, "Cấp bậc"),
        "working form": extract_general_info_value(soup, "Hình thức làm việc"),
        "salary_raw": salary_raw,
        "crawl_date": datetime.now().strftime("%Y-%m-%d"),
        "source_url": url,
        "source": SOURCE,
    }

    return data

import os

def load_crawled_urls(output_csv: str) -> set[str]:
    if not os.path.exists(output_csv):
        return set()

    crawled_urls = set()

    try:
        with open(output_csv, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("source_url", "")
                if url:
                    crawled_urls.add(url)
    except Exception as e:
        print(f"Không đọc được CSV cũ để resume: {e}")

    return crawled_urls

def crawl_topcv_it(
    start_url: str,
    output_csv: str,
    max_pages: int,
    delay_min: float,
    delay_max: float,
    resume: bool = False,
):
    session = requests.Session()
    session.headers.update(HEADERS)

    all_job_urls = []
    seen_urls = set()

    print("Bắt đầu lấy link job từ trang danh sách...")
    empty_page_count = 0
    for page in range(1, max_pages + 1):
        page_url = build_page_url(start_url, page)
        print(f"[LIST] Page {page}: {page_url}")

        try:
            soup = get_soup(session, page_url)
            job_urls = extract_job_links_from_list_page(soup, page_url)
        except KeyboardInterrupt:
            print("\nBạn đã dừng chương trình khi đang lấy danh sách link.")
            break
        except Exception as e:
            print(f"  Lỗi lấy page {page}: {e}")
            continue

        new_count = 0

        for job_url in job_urls:
            if job_url not in seen_urls:
                seen_urls.add(job_url)
                all_job_urls.append(job_url)
                new_count += 1
        print(f"  Tìm thấy {len(job_urls)} link, mới {new_count} link.")

        # Không dùng new_count để dừng, vì khi resume hoặc page bị trùng link,
        # new_count có thể = 0 dù vẫn chưa quét hết các page.
        if len(job_urls) == 0:
            empty_page_count += 1
            print(f"  Page này không có job. Empty count = {empty_page_count}")

            if empty_page_count >= 3:
                print("  Gặp 3 page liên tiếp không có job, dừng pagination.")
                break
        else:
            empty_page_count = 0

        time.sleep(random.uniform(delay_min, delay_max))

    print(f"\nTổng số job detail sẽ crawl: {len(all_job_urls)}")

    failed_urls = []
    success_count = 0
    skipped_count = 0

    crawled_urls = load_crawled_urls(output_csv) if resume else set()

    if resume:
        print(f"Resume mode: tìm thấy {len(crawled_urls)} URL đã có trong CSV.")

    file_exists = os.path.exists(output_csv)
    mode = "a" if resume and file_exists else "w"
    write_header = not (resume and file_exists)

    with open(output_csv, mode, encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_FIELDS,
            quoting=csv.QUOTE_ALL,
        )

        if write_header:
            writer.writeheader()

        for idx, job_url in enumerate(all_job_urls, start=1):
            if resume and job_url in crawled_urls:
                skipped_count += 1
                continue
            print(f"[DETAIL] {idx}/{len(all_job_urls)}: {job_url}")

            try:
                row = crawl_job_detail(session, job_url)

                # Đảm bảo không bị lỗi nếu thiếu field nào đó
                safe_row = {
                    field: row.get(field, "")
                    for field in CSV_FIELDS
                }

                writer.writerow(safe_row)
                f.flush()

                success_count += 1
                print(f"  OK - đã lưu dòng {success_count}")

            except KeyboardInterrupt:
                print("\nBạn đã dừng chương trình.")
                print("Các job đã crawl trước đó vẫn được lưu trong CSV.")
                break

            except Exception as e:
                print(f"  Lỗi crawl detail: {e}")
                failed_urls.append(job_url)

            time.sleep(random.uniform(delay_min, delay_max))

    if failed_urls:
        with open("failed_topcv_urls.txt", "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(url + "\n")

        print(f"\nĐã lưu {len(failed_urls)} URL lỗi vào failed_topcv_urls.txt")

    print("\nHoàn tất.")
    print(f"  Lưu mới: {success_count}")
    print(f"  Bỏ qua do đã có trong CSV: {skipped_count}")
    print(f"  File CSV: {output_csv}")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Crawl TopCV IT Software jobs to CSV")
    parser.add_argument("--resume", action="store_true", help="Bỏ qua URL đã có trong CSV output")
    parser.add_argument("--url", default=START_URL, help="URL trang danh sách TopCV")
    parser.add_argument("--output", default="topcv_it_jobs.csv", help="Tên file CSV output")
    parser.add_argument("--max-pages", type=int, default=3, help="Số trang danh sách muốn crawl")
    parser.add_argument("--delay-min", type=float, default=1.5, help="Delay thấp nhất giữa request")
    parser.add_argument("--delay-max", type=float, default=3.5, help="Delay cao nhất giữa request")

    args = parser.parse_args()

    crawl_topcv_it(
        start_url=args.url,
        output_csv=args.output,
        max_pages=args.max_pages,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        resume=args.resume,
    )