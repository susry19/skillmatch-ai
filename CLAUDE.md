# SkillMatch AI v4 — Proje Rehberi

FastAPI + SQLAlchemy backend, tek sayfa Vue 3 (CDN, build adımı yok) frontend'e sahip bir
İK / ATS (Applicant Tracking System) uygulaması. Otel zincirleri için çok-otelli (multi-hotel)
işe alım, kadro planlama ve aday yönetimi sistemi.

## Mimari Özet

- **Backend**: `backend/main.py` FastAPI giriş noktası. Router'lar `backend/routers/*.py`,
  iş mantığı `backend/services/*.py`, ORM modelleri `backend/models.py`, Pydantic şemaları
  `backend/schemas.py` içinde.
- **Frontend**: Tek dosya `backend/static/app.js` (~3500 satır) + `backend/static/style.css`
  (~1600 satır) + `backend/templates/index.html` (~6600 satır, tüm sayfa şablonları burada).
  Vue 3 `unpkg.com` CDN'den global build olarak yükleniyor — npm/webpack/vite yok, build adımı yok.
  Değişiklik yapınca sadece dosyayı kaydetmek yeterli; tarayıcıyı yenile.
- **Veritabanı**: Varsayılan SQLite (`sqlite:///./skillmatch.db`, backend/ içinde oluşur).
  Prod'da (Railway) PostgreSQL kullanılıyor. Şema migrasyonları **Alembic değil**,
  `backend/database.py` ve `backend/main.py` içinde elle yazılmış idempotent
  `ALTER TABLE ... ADD COLUMN` sorguları ile startup sırasında otomatik uygulanıyor
  (bkz. main.py içindeki `queries` listesi). Yeni kolon eklerken bu listeye satır eklemek gerekir.
- **Auth**: JWT tabanlı, `backend/auth.py`. Roller: `ADMIN`/`SYSTEM_ADMIN`, `HR`, `MANAGER`,
  `CANDIDATE`. Dinamik rol/izin sistemi de var (`role_id` → `models.Role.permissions`).
  Çok-otelli veri görünürlüğü `data_visibility_scope` + `hotel_access_ids` ile scope'lanıyor.
- **AI**: Google Gemini (`google-generativeai` — **deprecated**, bkz. Bilinen Sorunlar).
  CV parsing (`pdf_parser.py`), aday eşleştirme (`llm_matcher.py`, `matcher.py`), mülakat
  soru üretimi, chatbot (`services/chatbot.py`).

## Ortam Kurulumu (tamamlandı)

- Proje Python **3.11** gerektiriyor (`.python-version`, `runtime.txt`). Sistemde 3.14 de kurulu
  olduğundan venv özellikle `C:\Users\beyza.cetin\AppData\Local\Programs\Python\Python311\python.exe`
  ile oluşturuldu: `./venv/Scripts/python.exe`.
- Bağımlılıklar `requirements.txt`'ten kuruldu, 16/16 pytest testi geçiyor.
- `backend/.env` dosyası oluşturuldu (git'e girmiyor, `.gitignore`'da). Varsayılan SQLite
  kullanıyor, `GEMINI_API_KEY` boş — AI özellikleri (CV parse, matching, chatbot) key
  girilmeden çalışmaz.
- Sunucuyu başlatmak için: `backend/` içinden
  `../venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000`
  (main.py `backend` dizinini `sys.path`'e ekliyor ve `from database import ...` gibi relative
  importlar kullanıyor — bu yüzden çalışma dizini **mutlaka `backend/`** olmalı, repo kökünden
  değil).
- Demo giriş: `demo@skillmatch.ai` / `demo123` (ADMIN rolü, startup'ta otomatik oluşturuluyor/resetleniyor).
- `backend/.env.example` içinde gerçek görünen bir Gemini API key committed durumda —
  **bunu kullanma**, muhtemelen sızmış/iptal edilmiş bir key. Kullanıcıya bildir, kendi key'ini girmesini iste.

## Tema / Tasarım Sistemi Kuralları

Tüm renk, spacing, radius, shadow değerleri `backend/static/style.css` en üstündeki
`:root` bloğunda **design token** olarak tanımlı. **Yeni bileşen yazarken ham hex/px değeri
gömme — her zaman var olan bir `--color-*` / `--radius-*` / `--shadow-*` token'ını kullan.**

- **Marka rengi**: koyu yeşil `--color-primary: #173D34` (hover: `#1F5A49`), vurgu rengi
  `--color-accent: #2D7661`. Nötr arka plan `--color-mint: #EAF3EF`.
- **Tek tema** — dark mode / `prefers-color-scheme` desteği **yok**. Yeni bir sayfa/bileşen
  eklerken dark mode düşünmeye gerek yok, ama mevcut açık tema paletine sadık kal.
- Durum rozetleri (badge) için ayrı bir palet var: `--color-success-*`, `--color-warning-*`,
  `--color-danger-*`, `--color-info-*`, `--color-purple-*` — pipeline durumları
  (`b-applied`, `b-screening`, `b-interview`, `b-offer`, `b-hired`, `b-rejected`) bunları kullanıyor.
  Yeni bir durum eklerken bu beşliden en yakın anlamlısını seç, yeni renk icat etme.
- CSS'te **"Backward Compatibility Mapping"** bölümü var (`--primary`, `--g100`...`--g900`,
  `--green`, `--red` vb.) — eski kod bu kısa isimleri kullanıyor. Yeni kod yazarken uzun
  `--color-*` isimlerini tercih et, ama eski kısa isimleri kaldırma/yeniden adlandırma
  (çok sayıda yerde referans var, geniş çaplı regresyon riski taşır).
- Font: UI için `Inter` (`--font-ui`), başlık/display için `Georgia` (`--font-display`).
  Taban font-size `12px` — bu proje bilinçli olarak kompakt/yoğun bir bilgi yoğunluğu hedefliyor,
  büyütme önerisi gündeme gelirse önce sebebini sor.

## Bilinen Sorunlar / Dikkat Edilecekler

- `google-generativeai` paketi **deprecated** (startup loglarında `FutureWarning` üretiyor).
  Uzun vadede `google-genai` paketine geçiş gerekecek; bu geçiş `services/gemini_service.py`,
  `services/translator.py`, `services/ai_analyzer.py` gibi birden fazla dosyayı etkiler —
  büyük bir refactor, tek seferde yapılmamalı.
  Ayrıntı: [dev README](https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md)
- `sentence-transformers` kurulu değil → semantic matching keyword-based fallback'e düşüyor
  (`services/semantic_matcher.py` startup'ta uyarı basıyor). Kasıtlı bir hafif-kurulum kararı
  olabilir; kaldırmadan önce neden opsiyonel bırakıldığını sorgula.
- Pydantic v2 kullanılıyor ama `schemas.py` içinde çok sayıda class-based `class Config` var
  (deprecated, `ConfigDict` yerine). pytest'te ~28 deprecation warning üretiyor ama testleri
  bozmuyor. Dokunacaksan tek dosya içinde tutarlı kalması için toplu değiştir, tek tek değil.
- `backend/database.py` ve `backend/main.py` içindeki elle yazılmış `ALTER TABLE` migrasyonları
  SQLite ve PostgreSQL arasında sözdizimi farkına duyarlı olabilir (örn. `DROP NOT NULL` PG'ye
  özgü) — try/except ile sessizce yutuluyor, yani SQLite'ta bazı ALTER'lar sessizce başarısız
  olabilir. Yeni kolon eklerken hem SQLite hem PG üzerinde davranışı doğrula.
- `main.py` en dış katmanda `try/except` ile tüm startup'ı sarmalıyor ve hata durumunda
  "Fallback Diagnostic Server" döndürüyor (traceback'i HTML olarak expose ediyor). Bu prod'da
  bilgi sızıntısı riski taşır — hızlı debug için bilinçli tercih edilmiş, ama Railway dışına
  taşımadan önce bu davranışı gözden geçir.

## Genel Kurallar

- Migration eklerken Alembic'i değil, mevcut idempotent `ALTER TABLE` listesi desenini kullan
  (repo genelinde tutarlılık için — bkz. Mimari Özet).
- Frontend'de yeni bir sayfa/view eklerken `index.html` içine şablon, `app.js` içine state/metod
  ekleme desenini takip et; ayrı bir `.vue` dosyası veya build sistemi **ekleme** (proje bilinçli
  olarak build-free tutulmuş).
- Yeni router eklerken `main.py` içinde `app.include_router(...)` satırına eklemeyi unutma —
  router dosyası tek başına otomatik keşfedilmiyor.

  # CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

