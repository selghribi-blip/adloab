# Adloab Uptime — نظام مراقبة مواقع (Synthetic Monitoring)

نظام خفيف يراقب **المواقع التي تملكها**: يفحصها دوريًا، يقيس زمن الاستجابة على مراحل،
يرصد انتهاء شهادات SSL، يفتح حوادث عند التوقف، ويرسل تنبيهات. كل شيء مجاني ومفتوح المصدر.

> ⚠️ نطاق الاستخدام: هذا النظام مخصّص لمراقبة مواقعك أنت أو مواقع لديك إذن صريح بفحصها.
> فيه **حاجز ملكية** إلزامي: أي نطاق غير مذكور في `config/owned_domains.yaml` يُرفض فحصه.
> النظام ليس أداة لتوليد زيارات أو التلاعب بتحليلات مواقع الآخرين — ولا يوفّر أي قدرة من هذا النوع.

---

## لماذا هذا بدل ما طلبته؟

| ما طلبته | ما يقدّمه Adloab Uptime |
|---|---|
| Scrapy + متصفح + طابور مهام | httpx غير متزامن + طابور فحوصات بمجدول + دعم Playwright اختياري |
| بروكسي دوّار وتغيير بصمة | ❌ غير موجود — لأنه لا معنى له في مراقبة موقعك، ووجودته تخصّ التلاعب |
| "زيارات يصعب كشفها" | رصد حقيقي لموقعك: زمن، أخطاء، SSL، حوادث، تنبيهات |
| مجاني بالكامل | Python + SQLite + GitHub Actions — بلا أي تكلفة |

النتيجة: نفس المهارات الهندسية (asyncio، مؤشرات أداء، متصفح آلي، CI) لكن في مشروع
يُقوّي سيرتك الذاتية بدل أن يضرّ بغيرك ويحجب حسابك.

---

## التشغيل السريع

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) أضف نطاقك إلى قائمة الملكية
nano config/owned_domains.yaml

# 2) أضف الأهداف والفترات
nano config/targets.yaml

# 3) شغّل اللوحة  →  http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

فحص واحد من سطر الأوامر (مناسب لـ cron أو CI):

```bash
python -m app.cli check          # فحص فوري، يخرج بكود 1 عند وجود هدف متوقف
python -m app.cli check --json   # نتائج JSON للأنظمة الأخرى
python -m app.cli status         # ملخّص آخر 24 ساعة
python -m app.cli domains        # النطاقات المسموح بفحصها
python -m app.cli test-alert     # رسالة تجريبية إلى Telegram
python -m app.cli telegram-id    # معرفة رقم محادثتك (chat_id)
```

> ملاحظة: الفحوصات تحتاج اتصالًا خارجيًا بالإنترنت. داخل بيئات معزولة (sandbox) ستبدو
> الأهداف الخارجية «متوقفة» — هذا متوقع؛ الهدف المحلي «فحص ذاتي» يعمل في كل الحالات.
> استخدم `http://127.0.0.1:8000/healthz` كهدف لتتأكد أن المحرّك نفسه سليم.

## ما يُقاس في كل فحص

- `dns_ms` — زمن تحليل الاسم
- `connect_ms` — زمن المصافحة (TLS)
- `ttfb_ms` — الزمن حتى أول بايت من الاستجابة
- `total_ms` — الاستماع الكامل للصفحة (حتى حدّ 64KB)
- `status_code` + التحقق من رمز متوقع ونص متوقع داخل الصفحة
- `tls_days_left` — الأيام المتبقية لانتهاء الشهادة (تنبيه تلقائي تحت 7 أيام)
- فحص متصفح اختياري (Playwright): عنوان الصفحة، عدّاد أخطاء console، زمن التحميل الفعلي

## تنبيهات Telegram (مجانية بالكامل)

يُرسل النظام أربعة أنواع من التنبيهات: **توقف** 🔴 · **عودة للعمل** 🟢 ·
**بطء متكرر** 🐢 · **قرب انتهاء شهادة SSL** 🔐 — مع فترة تهدئة تمنع الإغراق.

### الإعداد في 3 دقائق

```bash
# 1) من داخل Telegram: افتح @BotFather ← /newbot ← انسخ التوكن
# 2) أرسل أي رسالة إلى بوتك الجديد، ثم:
export TELEGRAM_BOT_TOKEN="123456789:AAxxxxxxxxxxxxxxxxx"
python -m app.cli telegram-id        # يعرض رقم محادثتك (chat_id)
export TELEGRAM_CHAT_ID="-1001234567890"

# 3) تحقق من الوصول:
python -m app.cli test-alert         # يجيب: ✅ تم الإرسال — راجع Telegram الآن
```

> 🔐 **قاعدة أمنية**: رمز البوت = تحكم كامل بالبوت. لا تكتبه في `config/alerts.yaml`
> ولا في أي ملف يُرفع إلى Git. ضعه في `.env` (مستبعد في `.gitignore`) أو في
> GitHub Secrets. انسخ `.env.example` للبدء.

بديل أبسط: `chmod 600 .env` ثم `set -a; source .env; set +a` قبل تشغيل اللوحة.
تُقرأ المتغيرات أيضًا تلقائيًا في Docker Compose من ملف `.env` المجاور.

### من اللوحة

في أعلى الصفحة زر **«تنبيه تجريبي»**، وقسم **«قناة التنبيهات»** يعرض حالة القناة
دون كشف التوكن (يظهر آخر 4 أحرف فقط): `Telegram ✅ (…9xYz → chat 123456789)`.

### متى يُنبَّه؟

| الحالة | التنبيه | التوقيت |
|---|---|---|
| إخفاق متتالٍ (عدد `failure_threshold`) | 🔴 توقف | فورًا، **مرة واحدة لكل حادثة** |
| عودة الموقع بعد حادثة | 🟢 عودة للعمل | فورًا عند أول نجاح |
| `latency_alert_ms` متجاوَز `latency_consecutive` مرات | 🐢 بطء | بعد تكرار البطء لا ارتفاع عابر |
| `tls_days_left ≤ tls_warn_days` | 🔐 شهادة SSL | مرة كل يوم كحد أقصى |

كل هذه القيم (وبدء التشغيل عبر Webhook بدل/إضافة إلى Telegram) في `config/alerts.yaml`.

### في GitHub Actions

أضف السرّين `TELEGRAM_BOT_TOKEN` و`TELEGRAM_CHAT_ID` في
`Settings → Secrets and variables → Actions`، وسير عمل `monitor.yml` سيُرسل
تنبيهات Telegram كل 15 دقيقة بلا أي سيرفر دائم.

## الجدولة المجانية عبر GitHub Actions

الملف `.github/workflows/monitor.yml` يشغّل فحصًا كل 15 دقيقة على مستودع عام (مجاني)،
ويفشل الـ job عند توقف هدف — فتصلك رسالة بريد تلقائية من GitHub. أضف في
`Settings → Secrets` المتغير `ADLOAB_EXTRA_DOMAINS` بنطاقك إن أردت عدم تخزينه في الملف.

## التخزين: SQLite أو Postgres

الافتراضي SQLite (ملف واحد، بلا سيرفر). للتبديل إلى Postgres (تاريخ أطول، أو عدة نسخ
من اللوحة تعمل معًا) ضع متغير البيئة فقط:

```bash
export ADLOAB_DB_URL="postgresql://adloab:adloab@localhost:5432/adloab"
uvicorn app.main:app --host 0.0.0.0 --port 8000    # يلاحظ الفرق تلقائيًا
```

أو بأمر واحد عبر Docker:

```bash
docker compose up        # Postgres + اللوحة معًا
```

المحدِّد في `app/store.py`، والتنفيذان يتشاركان نفس الحسابات في `app/stats.py`.
الاختبارات تغطي الخلفيتين: `tests/test_core.py` (SQLite) و`tests/test_postgres_backend.py`
(Postgres حقيقي — يشغّله الاختبار تلقائيًا عبر `pgserver` إن لم يكن لديك خادم).

## اختبار الحمل (لمواقعك فقط)

```bash
# بديل بلا تثبيت — يعمل فورًا
python loadtest/py_load.py --url http://127.0.0.1:8000/healthz --vus 20 --duration 30 --i-own-this-site

# مسار k6 الكامل (smoke / load / stress)
python loadtest/run.py --url https://staging.mysite.ma --scenario load --vus 30 --duration 2m --i-own-this-site
```

كلاهما يمر عبر **حاجز الملكية** نفسه: نطاق غير مدرج في `config/owned_domains.yaml` = رفض فوري.
التفاصيل والأرقام المرجعية في [`loadtest/README.md`](loadtest/README.md).

> ⚠️ لا تشغّل `stress` على الإنتاج — استخدم نسخة staging. اختبار الحمل على موقع لا تملكه
> يُعدّ هجوم حجب خدمة (DoS) وهو مخالف للقانون ولشروط مزوّدي الاستضافة.

## اختبارات المتصفح (E2E) وBrowserStack

نفس الاختبارات تعمل في ثلاثة أوضاع بلا تعديل:

```bash
pytest tests/e2e -q                          # 1) Chromium محلي (يشغّل اللوحة تلقائيًا)
E2E_BASE_URL=https://staging.mysite.ma pytest tests/e2e -q   # 2) موقعك
BROWSERSTACK_USERNAME=... BROWSERSTACK_ACCESS_KEY=... \
  BROWSERSTACK_BROWSER=safari BROWSERSTACK_OS="OS X" pytest tests/e2e -q   # 3) متصفح حقيقي
```

تغطّي: اتجاه RTL، رسم البطاقات، شارات الحالة، زر «افحص الآن»، ظهور قائمة النطاقات المصرّح بها،
خلوّ الصفحة من أخطاء console، والتجاوب على مقاسات الجوال والتابلت.

## بنية المشروع

```
app/
  config.py        الإعدادات + حاجز الملكية (Ownership Guard)
  store.py         محدِّد خلفية التخزين (SQLite / Postgres)
  db.py            خلفية SQLite: فحوصات، إحصاءات، حوادث
  db_postgres.py   خلفية Postgres بنفس الواجهة
  stats.py         حسابات مشتركة (p95، نسبة التوفّر)
  checker.py       محرّك الفحص: DNS/TLS/TTFB + فحص المتصفح + التحقق من المحتوى
  scheduler.py     مجدول غير متزامن + إدارة الحوادث
  alerts.py        Telegram Bot API + Webhook + تهدئة التنبيهات
  main.py          واجهة FastAPI + API
  cli.py           سطر الأوامر
  static/          لوحة تحكم عربية RTL بلا أي مكتبة خارجية
config/            owned_domains.yaml (الملكية) + targets.yaml (الأهداف) + alerts.yaml (التنبيهات)
.env.example       قالب متغيرات البيئة (التوكن والرقم) — انسخه إلى .env
loadtest/          k6 (smoke/load/stress) + بديل asyncio + حاجز الملكية
tests/             pytest: النواة + خلفية Postgres
tests/e2e/         Playwright: محليًا / موقعك / BrowserStack
Dockerfile · docker-compose.yml   تشغيل اللوحة مع Postgres
.github/workflows/  مراقبة دورية · اختبارات Postgres · E2E · اختبار حمل
```

## واجهة API

| المسار | الوظيفة |
|---|---|
| `GET /api/status` | حالة كل الأهداف + إحصاءات 24 ساعة |
| `GET /api/targets/{id}/checks?limit=60` | سلسلة الفحوصات للرسم البياني |
| `POST /api/targets/{id}/check` | فحص فوري لهدف |
| `POST /api/check-all` | فحص كل الأهداف |
| `GET /api/incidents` | سجل الحوادث |
| `GET /api/config/domains` | النطاقات المسموح بفحصها |
| `POST /api/alerts/test` | إرسال تنبيه تجريبي للقنوات المهيّأة |

## الاختبارات

```bash
pip install -r requirements-dev.txt
pytest -q                 # النواة + Postgres + E2E (يتخطى ما لا يستطيع تشغيله بلطف)
pytest tests/e2e -q       # اختبارات المتصفح فقط
```

| الملف | يغطّي |
|---|---|
| `tests/test_core.py` | حاجز الملكية، النطاقات الشبيهة، الإحصاءات، دورة الحوادث |
| `tests/test_postgres_backend.py` | خلفية Postgres على خادم حقيقي (أو تتخطى نفسها) |
| `tests/test_alerts.py` | قناة Telegram: شكل الطلب، إعادة المحاولة، التهدئة، التهريب، وتكامل HTTP حقيقي |
| `tests/e2e/test_dashboard.py` | عقد API + سلوك اللوحة على متصفح حقيقي |

---

## استغلال GitHub Student Pack بشكل مشروع

| الأداة | الاستخدام المشروع في هذا المشروع |
|---|---|
| **GitHub Actions** | جدولة الفحوصات كل 15 دقيقة + CI (اختبارات Postgres، E2E، اختبار حمل ذاتي) مجانًا على المستودعات العامة |
| **BrowserStack** (خطة الطلاب) | تشغيل `tests/e2e` على Chrome وFirefox وSafari وأجهزة حقيقية — `.github/workflows/e2e.yml` |
| **DigitalOcean / Render / Railway** أرصدة | استضافة اللوحة 24/7 مع `docker compose up` (Postgres + اللوحة) |
| **Namecheap / .me** | نطاق لمشروعك + شهادة SSL حقيقية لتراقبها (اختبرها بانتهاء قريب) |
| **Copilot / JetBrains** | تطوير اللوحة نفسها |
| **Telegram Bot API** | مجاني تمامًا وبلا حدود عملية لتنبيهاتك — لا يحتاج خطة مدفوعة |

### تفعيل BrowserStack في 4 خطوات

1. فعّل حزمة الطلاب: <https://education.github.com/pack> → BrowserStack.
2. وقّع دخولك على <https://www.browserstack.com> من صفحة الحزمة، ثم
   `Account → Settings → Access Key` وانسخ: **Username** و **Access Key**.
3. أضفهما في مستودعك: `Settings → Secrets and variables → Actions → New repository secret`:
   `BROWSERSTACK_USERNAME` و `BROWSERSTACK_ACCESS_KEY`.
4. شغّل سير العمل `.github/workflows/e2e.yml` يدويًا وأدخل `base_url` = رابط موقعك العام.
   المتصفحات تتصل من خوادم BrowserStack، لذا يجب أن يكون الرابط **متاحًا للعامة**
   (أو فعّل `BROWSERSTACK_LOCAL=true` مع نفق BrowserStack Local).

لتوسيع التغطية: أضف تركيبات جديدة في `strategy.matrix` داخل الملف نفسه (مثل iPhone أو Android).

## الترخيص

MIT — استخدمه، طوّره، وشاركه.
