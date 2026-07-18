import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def download_cfx_weapon_images():
    # URL của trang vũ khí trên Cfx.re Docs
    url = "https://docs.fivem.net/docs/game-references/weapon-models/"
    base_url = "https://docs.fivem.net"
    save_dir = "cfx_weapon_images"

    # Tạo thư mục chứa ảnh nếu chưa có
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print("Đang truy cập trang web Cfx.re Docs...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Không thể truy cập trang web: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # FiveM Docs sử dụng Docusaurus, nội dung chính thường nằm trong thẻ <article>
    content = soup.find('article')
    if not content:
        print("Không tìm thấy thẻ <article>, sẽ tiến hành tìm trên toàn bộ trang...")
        content = soup

    # Tìm tất cả thẻ img
    images = content.find_all('img')
    print(f"Tìm thấy {len(images)} ảnh. Bắt đầu tải...\n")

    count = 0
    for img in images:
        img_url = img.get('src')
        if not img_url:
            continue

        # Đảm bảo đường dẫn là URL tuyệt đối
        img_url = urljoin(base_url, img_url)

        # Lấy tên file gốc (bỏ các tham số dấu ? ở cuối URL nếu có)
        filename = os.path.basename(img_url.split('?')[0])

        # Lọc để chỉ tải các định dạng ảnh thông dụng
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
            continue

        try:
            # Tải nội dung ảnh
            img_data = requests.get(img_url, headers=headers).content
            filepath = os.path.join(save_dir, filename)
            
            # Ghi file vào thư mục
            with open(filepath, 'wb') as handler:
                handler.write(img_data)
            print(f"[+] Đã tải: {filename}")
            count += 1
        except Exception as e:
            print(f"[-] Lỗi khi tải {img_url}: {e}")

    print(f"\n✅ Hoàn tất! Đã tải thành công {count} ảnh vào thư mục '{save_dir}'.")

if __name__ == "__main__":
    download_cfx_weapon_images()