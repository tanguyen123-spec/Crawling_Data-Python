from data_scraper import scrape_data
import time

def main():
    base_url = "https://www.newegg.com/p/pl?N=100006662&PageSize=96&page="
    total_pages = 41
    start_time = time.time()  # Bắt đầu đếm thời gian
    for current_page in range(1, total_pages + 1):
        url = base_url + str(current_page)
        print(f"Đang lấy dữ liệu từ trang: {current_page}, URL: {url}")
        scrape_data(url)
        print(f"Đã hoàn thành lấy dữ liệu từ trang {current_page}")

    end_time = time.time()  # Kết thúc đếm thời gian
    total_time = end_time - start_time  # Tính tổng thời gian thực thi

    print(f"Tổng thời gian thực thi: {total_time} giây")

if __name__ == "__main__":
    main()
