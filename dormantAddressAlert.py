import requests
import time
import os
from plyer import notification
from playsound import playsound

BTC_ADDRESSES_TO_WATCH = [
    "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
    "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ",
]

CHECK_INTERVAL_SECONDS = 60
SOUND_FILE_PATH = "alert.wav"

last_known_tx = {}

def get_latest_transaction(address):
    try:
        url = f"https://blockstream.info/api/address/{address}/txs"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        transactions = response.json()
        if transactions:
            return transactions[0]
        return None
    except requests.exceptions.RequestException as e:
        print(f"HATA: API'ye bağlanırken bir sorun oluştu: {e}")
        return None
    except ValueError:
        print(f"HATA: API'den gelen yanıt JSON formatında değil. Adres: {address}")
        return None

def format_transaction_details(tx):
    txid = tx['txid']
    total_output_satoshi = sum(vout['value'] for vout in tx['vout'])
    total_output_btc = total_output_satoshi / 100_000_000
    is_confirmed = tx['status']['confirmed']
    status_str = "Onaylandı" if is_confirmed else "Onay Bekliyor"
    return f"Toplam Miktar: {total_output_btc:.4f} BTC\nDurum: {status_str}\nTXID: {txid[:20]}..."

def send_notification_alert(address, tx_details):
    print(">>> YENİ İŞLEM TESPİT EDİLDİ! Bildirim gönderiliyor...")
    try:
        notification.notify(
            title="🐳 WhaleAlert: Yeni BTC İşlemi!",
            message=f"Adres: {address[:10]}...\n{tx_details}",
            app_name="WhaleAlert",
            timeout=20
        )
    except Exception as e:
        print(f"HATA: Masaüstü bildirimi gönderilemedi: {e}")
    try:
        if os.path.exists(SOUND_FILE_PATH):
            playsound(SOUND_FILE_PATH)
        else:
            print(f"UYARI: Ses dosyası bulunamadı: {SOUND_FILE_PATH}")
    except Exception as e:
        print(f"HATA: Ses dosyası çalınırken bir sorun oluştu: {e}")

def main():
    print("="*40)
    print("WhaleAlert Başlatıldı!")
    print(f"İzlenen Adres Sayısı: {len(BTC_ADDRESSES_TO_WATCH)}")
    print(f"Kontrol Aralığı: {CHECK_INTERVAL_SECONDS} saniye")
    print("="*40)
    for address in BTC_ADDRESSES_TO_WATCH:
        print(f"'{address[:10]}...' adresi için başlangıç durumu alınıyor...")
        latest_tx = get_latest_transaction(address)
        if latest_tx:
            last_known_tx[address] = latest_tx['txid']
            print(f"-> Son işlem ID'si kaydedildi: {last_known_tx[address][:20]}...")
        else:
            last_known_tx[address] = None
            print(f"-> Bu adreste henüz işlem bulunamadı.")
        time.sleep(1)
    print("\nİzleme döngüsü başladı. Yeni işlemler bekleniyor...")
    while True:
        for address in BTC_ADDRESSES_TO_WATCH:
            latest_tx = get_latest_transaction(address)
            if latest_tx:
                current_txid = latest_tx['txid']
                if address in last_known_tx and last_known_tx[address] != current_txid:
                    tx_details_str = format_transaction_details(latest_tx)
                    print(f"\n!!! YENİ İŞLEM: {address} adresinde hareket algılandı!")
                    print(tx_details_str)
                    send_notification_alert(address, tx_details_str)
                    last_known_tx[address] = current_txid
        print(f".", end='', flush=True)
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
