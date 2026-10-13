import requests

# ВСТАВЬТЕ ВАШ ТОКЕН СЮДА НАПРЯМУЮ ДЛЯ ТЕСТА (без пробелов):
API_KEY_DIRECT = "ВАШ_РЕАЛЬНЫЙ_ТОКЕН_С_САЙТА"

def run_direct_network_test():
    print("=" * 60)
    print("ПРЯМОЙ ТЕСТ СЕТЕВОГО ЗАПРОСА БЕЗ .ENV")
    print("=" * 60)
    
    url = "https://kinopoiskapiunofficial.tech"
    headers = {
        "X-API-KEY": API_KEY_DIRECT,
        "Content-Type": "application/json"
    }
    
    try:
        print("Отправка прямого GET-запроса на сервер...")
        response = requests.get(url, headers=headers, timeout=5)
        
        print(f"\n[ОТВЕТ СЕРВЕРА]:")
        print(f" -> Код статуса: {response.status_code}")
        print(f" -> Тело ответа: {response.text}")
        
        if response.status_code == 200:
            print("\n УСПЕХ: Сервер принял ключ напрямую! Ключ рабочий.")
        else:
            print("\n СБОЙ: Проверьте, точно ли этот токен скопирован из ЛК.")
            
    except Exception as e:
        print(f"\n Ошибка подключения: {e}")
    print("=" * 60)

if __name__ == "__main__":
    run_direct_network_test()
