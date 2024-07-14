import os
import re
import json
import time
from urllib.parse import urljoin
from singleton import Scraper

# Hàm chính để lấy dữ liệu từ trang web
def scrape_data(url):
    scraper = Scraper()  # Tạo đối tượng Scraper (singleton)

    # Đường dẫn tới các tệp cần sử dụng
    last_processed_url_file = "last_processed_url.txt"
    json_file = "ecommerce/Datacrawling.json"
    
    # Khởi tạo URL cuối cùng đã xử lý và trang hiện tại
    last_processed_url = None
    current_page = 1

    # Kiểm tra xem tệp last_processed_url_file có tồn tại không và đọc URL và trang hiện tại
    if os.path.exists(last_processed_url_file):
        with open(last_processed_url_file, "r") as f:
            data = f.read().strip().split(",")
            if len(data) == 2:
                last_processed_url = data[0]
                current_page = int(data[1])

    # Nạp dữ liệu hiện có từ tệp JSON hoặc khởi tạo danh sách trống
    if os.path.exists(json_file) and os.path.getsize(json_file) > 0:
        with open(json_file, "r", encoding="utf-8") as jsonf:
            try:
                existing_data = json.load(jsonf)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Tạo tập hợp các ID mục hiện có để tra cứu nhanh
    existing_item_ids = set(item["item_id"] for item in existing_data)

    # Nếu existing_data trống, bắt đầu lại từ đầu
    if not existing_data:
        last_processed_url = None
        current_page = 1

    response = scraper.fetch_page(url)  # Lấy nội dung trang web
    if response.status_code == 200:
        soup = scraper.fetch_soup(response.content)  # Phân tích nội dung HTML
        containers = soup.find_all("div", class_="item-container")  # Tìm tất cả các mục sản phẩm
        data_list = []  # Danh sách để lưu trữ dữ liệu mới
        total_data = 0  # Tổng số dữ liệu đã lấy được

        for container in containers:
            item_id = container.get("id")  # Lấy ID của mục

            # Kiểm tra xem item_id đã tồn tại trong dữ liệu JSON chưa
            if item_id in existing_item_ids:
                continue

            item_title = container.find("a", class_="item-title")
            item_title = item_title.text.strip() if item_title else "none"

            item_rating = 0
            item_rating_tag = container.find("div", class_="item-info").find("span")
            if item_rating_tag:
                item_rating_text = item_rating_tag.text.strip()
                rating_number = re.search(r'\((\d+)\)', item_rating_text)
                if rating_number:
                    item_rating = int(rating_number.group(1))

            item_rating_aria_label = 0.0
            item_rating_tag = container.find("i", class_=re.compile(r"rating rating-\d(?:-\d)?"))
            if item_rating_tag:
                aria_label = item_rating_tag.get("aria-label")
                if aria_label:
                    rating_match = re.search(r'rated (\d+(\.\d+)?) out of 5', aria_label)
                    if rating_match:
                        item_rating_aria_label = float(rating_match.group(1))

            item_price_after = container.find("li", class_="price-current")
            product_delivery = container.find("li", class_="price-ship").text.strip()
            item_image = container.find("img")["src"]
            
            item_title1 = container.find("a", class_="item-title")
            if item_title1 and item_title1.get("href"):
                item_href = item_title1["href"]
                new_url = urljoin(url, item_href)
                print(new_url)
            
            brand_title = None
            img_tag = container.find("a", class_="item-brand")
            if img_tag:
                img_tag = img_tag.find("img")
                if img_tag:
                    brand_title = img_tag.get('title')

            if last_processed_url and new_url == last_processed_url:
                continue

            new_response = scraper.fetch_page(new_url)  # Lấy nội dung trang sản phẩm chi tiết
            if new_response.status_code == 200:
                new_soup = scraper.fetch_soup(new_response.content)
                caption_item = new_soup.find("caption", string="Model")
                caption_item1 = new_soup.find("caption", string="Details")
                caption_item2 = new_soup.find("caption", string="Ports")
                caption_item3 = new_soup.find("caption", string="3D API")

                model = extract_detail(caption_item, "Model", "N/A")
                max_resolution = extract_detail(caption_item1, "Max Resolution", "N/A")
                display_port = extract_detail(caption_item2, "DisplayPort", "N/A")
                direct_x = extract_detail(caption_item3, "DirectX", "N/A")
                hdmi = extract_detail(caption_item2, "HDMI", "N/A")
            else:
                model = max_resolution = display_port = direct_x = hdmi = "N/A"

            price_shipping, shipping = process_shipping(product_delivery)
            item_price_after = process_price(item_price_after)
            total_price = (item_price_after if item_price_after is not None else 0) + price_shipping

            data_list.append(
                {
                    "item_id": item_id,
                    "item_title": item_title,
                    "item_rating": item_rating,
                    "item_rating_aria_label": item_rating_aria_label,
                    "item_price_after": item_price_after,
                    "price_shipping": price_shipping,
                    "product_delivery": shipping,
                    "item_image": item_image,
                    "max_resolution": max_resolution,
                    "display_port": display_port,
                    "hdmi": hdmi,
                    "direct_x": direct_x,
                    "model": model,
                    "total_price": total_price,
                    "new_url": new_url,
                    "brand_title": brand_title,
                }
            )

            # Ghi dữ liệu vào tệp văn bản
            with open("ecommerce/Datacrawling.txt", "a", encoding="utf-8") as file:
                file.write(f"Item ID: {item_id}\n")
                file.write(f"Item Title: {item_title}\n")
                file.write(f"Item Rating: {item_rating}\n")
                file.write(f"Item Rating Tag: {item_rating_aria_label}\n")
                file.write(f"Item Price After: {item_price_after}\n")
                file.write(f"Price: {price_shipping}\n")
                file.write(f"Shipping: {shipping}\n")
                file.write(f"Image Url: {item_image}\n")
                file.write(f"Max Resolution: {max_resolution}\n")
                file.write(f"DisplayPort: {display_port}\n")
                file.write(f"HDMI: {hdmi}\n")
                file.write(f"DirectX: {direct_x}\n")
                file.write(f"Model: {model}\n")
                file.write(f"Total Price: {total_price}\n")
                file.write(f"New URL: {new_url}\n")
                file.write(f"brand_title: {brand_title}\n")
                file.write("\n")

            total_data += 1

        existing_data.extend(data_list)
        with open(json_file, "w", encoding="utf-8") as jsonf:
            json.dump(existing_data, jsonf, ensure_ascii=False, indent=4)
        print(f"Dữ liệu đã được thu thập thành công và được thêm vào tệp Datacrawling.txt.")
        print(f"Tổng số dữ liệu đã lấy được: {total_data}")
    else:
        print(f"Lỗi: {response.status_code}")
        return existing_data

    # Lưu URL cuối cùng đã xử lý và trang hiện tại vào tệp
    with open(last_processed_url_file, "w") as f:
        f.write(f"{url},{current_page}\n")

    return existing_data

# Hàm để lấy chi tiết từ trang sản phẩm
def extract_detail(caption_item, text, default_value):
    if caption_item:
        table_product = caption_item.find_parent("table", class_="table-horizontal")
        if table_product:
            item_th = table_product.findAll("th")
            item_th_model = None
            for th in item_th:
                if th.text.strip() == text:
                    item_th_model = th
                    break
            if item_th_model:
                td_item = item_th_model.find_next_sibling("td")
                if td_item:
                    return td_item.text.strip()
    return default_value

# Hàm để xử lý chi phí vận chuyển
def process_shipping(product_delivery):
    shipping_parts = product_delivery.split()
    if len(shipping_parts) > 0:
        first_part = shipping_parts[0].replace("$", "")
        if first_part.isdigit():
            price_shipping = float(first_part)
            shipping = " ".join(shipping_parts[1:])
        else:
            try:
                price_shipping = float(first_part)
                shipping = " ".join(shipping_parts[1:])
            except ValueError:
                price_shipping = 0
                shipping = product_delivery
    else:
        price_shipping = 0
        shipping = product_delivery
    return price_shipping, shipping

# Hàm để xử lý giá sản phẩm
def process_price(item_price_after):
    try:
        if item_price_after:
            price_strong = item_price_after.find("strong")
            price_sup = item_price_after.find("sup")
            if price_strong and price_sup:
                price_strong = price_strong.string.strip()
                price_sup = price_sup.string.strip()
                price_strong = re.sub(r"[^\d]", "", price_strong)
                price_sup = re.sub(r"[^\d]", "", price_sup)
                return float(price_strong + "." + price_sup)
        return 0
    except AttributeError as e:
        print(f"AttributeError: {e}")
        return 0
    except Exception as e:
        print(f"Exception: {e}")
        return 0
