# SkillMatch AI v4 — Detaylı Kullanım ve Kurulum Kılavuzu

SkillMatch AI v4, yapay zeka destekli bir işe alım (ATS) platformudur. CV analizi, mülakat sorusu oluşturma, aday takip ve teklif yönetimi gibi özellikler sunar.

---

## 1. Hızlı Başlatma (Windows)

Uygulamayı en hızlı şekilde çalıştırmak için ana dizindeki `run.bat` dosyasını kullanabilirsiniz.

1.  **run.bat** dosyasına çift tıklayın.
2.  Bu işlem şunları yapacaktır:
    -   Eksik kütüphaneleri yükler (`pip install`).
    -   Veritabanını hazırlar (SQLite: `skillmatch.db`).
    -   Sunucuyu başlatır (`http://localhost:8000`).

---

## 2. Giriş Bilgileri ve İlk Kayıt

Sistemde şu an kayıtlı bir kullanıcı bulunmamaktadır. **Kayıt olan ilk kullanıcı otomatik olarak "ADMIN" yetkisi kazanır.**

### Önerilen İlk Yönetici Hesabı:
Uygulamayı açtıktan sonra kayıt olma ekranına giderek şu bilgileri kullanabilirsiniz:

-   **E-posta:** `admin@skillmatch.ai`
-   **Şifre:** `Admin1234!` (veya istediğiniz güçlü bir şifre)
-   **İsim:** `Sistem Yöneticisi`

**Giriş Linki:** [http://localhost:8000](http://localhost:8000)

---

## 3. Yapılandırma (.env)

Yapay zeka özelliklerinin (CV analizi, chatbot, mülakat soruları vb.) çalışması için `backend/.env` dosyasında geçerli bir API anahtarı olmalıdır.

**Mevcut GEMINI_API_KEY:** `YOUR_GEMINI_API_KEY_HERE` (Bu anahtar şu an dosyada tanımlıdır).

Eğer e-posta gönderimi (adaylara bildirim, teklif vb.) istiyorsanız, `.env` dosyasına şu satırları eklemelisiniz:

```env
MAIL_USERNAME=sizin-epostaniz@domain.com
MAIL_PASSWORD=eposta-uygulama-sifreniz
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

---

## 4. Manuel Kurulum Adımları (Geliştiriciler İçin)

Eğer terminal üzerinden manuel çalıştırmak isterseniz:

1.  **Terminali açın** ve proje dizinine gidin.
2.  **Sanal ortam oluşturun (Önerilir):**
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Bağımlılıkları yükleyin:**
    ```powershell
    pip install -r backend/requirements.txt
    ```
4.  **Uygulamayı başlatın:**
    ```powershell
    python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

---

## 5. Uygulama Linkleri

-   **Dashboard:** [http://localhost:8000](http://localhost:8000)
-   **API Dökümantasyonu (Swagger):** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
-   **Mevcut Veritabanı:** Proje kök dizinindeki `skillmatch.db` (SQLite) dosyasıdır.

---

## 6. Önemli Notlar

-   **Roller:** Kaydolan ilk kişi `ADMIN` olur, ondan sonrakiler kayıt sırasında seçtiği rolü (`HR`, `Manager`, `Candidate`) alır.
-   **AI Analizi:** Aday CV'lerini (PDF) "Adaylar" sekmesinden yüklediğinizde sistem otomatik olarak analiz eder ve puanlar.
-   **Mülakatlar:** Pozisyon detay sayfasından adaylar için yapay zeka tarafından özel hazırlanmış mülakat soruları oluşturabilirsiniz.
