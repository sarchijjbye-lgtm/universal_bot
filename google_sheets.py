import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEET_NAME

def connect_to_sheet():
    """Подключение к Google Sheets через JSON из переменных окружения."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_data = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not json_data:
        raise Exception("❌ GOOGLE_CREDENTIALS_JSON is missing in environment variables")
    
    creds_dict = json.loads(json_data)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    try:
        spreadsheet = client.open(GOOGLE_SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(GOOGLE_SHEET_NAME)
        # Создаём лист Orders
        orders_sheet = spreadsheet.sheet1
        orders_sheet.update_title("Orders")
        orders_sheet.append_row(["Время", "Клиент", "Заказ", "Адрес", "Сумма", "Оплата"])
        
        # Создаём лист Products
        products_sheet = spreadsheet.add_worksheet(title="Products", rows=100, cols=12)
        products_sheet.append_row([
            "id", "parent_id", "category", "name", "variant_label", 
            "price", "description", "our_price", "supplier", "stock", "file_id", "active"
        ])
    
    return spreadsheet

def get_orders_sheet(spreadsheet):
    """Получить лист заказов"""
    try:
        return spreadsheet.worksheet("Orders")
    except:
        return spreadsheet.sheet1

def get_products_sheet(spreadsheet):
    """Получить лист товаров"""
    try:
        return spreadsheet.worksheet("Products")
    except:
        # Создать если не существует
        products_sheet = spreadsheet.add_worksheet(title="Products", rows=100, cols=12)
        products_sheet.append_row([
            "id", "parent_id", "category", "name", "variant_label", 
            "price", "description", "our_price", "supplier", "stock", "file_id", "active"
        ])
        return products_sheet

def add_order(spreadsheet, username, items, address, total, phone):
    """
    Добавляет новую строку в таблицу заказов.
    """
    orders_sheet = get_orders_sheet(spreadsheet)
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        username,
        items,
        address,
        total,
        phone
    ]
    orders_sheet.append_row(row)
    print(f"✅ Добавлен заказ в таблицу: {username} — {total}₽")

def get_orders(spreadsheet):
    """
    Возвращает все заказы в виде списка словарей
    """
    try:
        orders_sheet = get_orders_sheet(spreadsheet)
        data = orders_sheet.get_all_records()
        print(f"📄 Загружено {len(data)} заказов из Google Sheets")
        return data
    except Exception as e:
        print(f"❌ Ошибка чтения заказов: {e}")
        return []

def load_products(spreadsheet):
    """
    Загружает все товары из листа Products
    Возвращает список словарей с полной информацией о товарах
    """
    try:
        products_sheet = get_products_sheet(spreadsheet)
        records = products_sheet.get_all_records()
        
        # Фильтруем только активные товары
        products = []
        for rec in records:
            # Проверяем active (может быть TRUE/True/true/1)
            active = str(rec.get("active", "")).strip().upper()
            if active in ["TRUE", "1", "YES"]:
                products.append({
                    "id": str(rec.get("id", "")).strip(),
                    "parent_id": str(rec.get("parent_id", "")).strip(),
                    "category": str(rec.get("category", "")).strip(),
                    "name": str(rec.get("name", "")).strip(),
                    "variant_label": str(rec.get("variant_label", "")).strip(),
                    "price": str(rec.get("price", "")).strip(),
                    "description": str(rec.get("description", "")).strip(),
                    "our_price": str(rec.get("our_price", "")).strip(),
                    "supplier": str(rec.get("supplier", "")).strip(),
                    "stock": str(rec.get("stock", "")).strip(),
                    "file_id": str(rec.get("file_id", "")).strip(),
                })
        
        print(f"📦 Загружено {len(products)} активных товаров из Products")
        return products
    except Exception as e:
        print(f"❌ Ошибка загрузки товаров: {e}")
        return []

def update_product_photo(spreadsheet, product_id, file_id):
    """
    Обновляет file_id для товара с указанным id
    """
    try:
        products_sheet = get_products_sheet(spreadsheet)
        all_values = products_sheet.get_all_values()
        
        # Найти строку с нужным id (первая колонка)
        for i, row in enumerate(all_values):
            if i == 0:  # Пропускаем заголовок
                continue
            if str(row[0]).strip() == str(product_id).strip():
                # Обновляем колонку file_id (индекс 10, т.е. K)
                products_sheet.update_cell(i + 1, 11, file_id)
                print(f"✅ Обновлено фото для товара ID={product_id}")
                return True
        
        print(f"⚠️ Товар с ID={product_id} не найден")
        return False
    except Exception as e:
        print(f"❌ Ошибка обновления фото: {e}")
        return False
