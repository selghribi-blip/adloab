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

## التنبيهات (مجانية)

ضع عنوان Webhook في `config/targets.yaml` أو في متغير البيئة `ALERT_WEBHOOK_URL`:

```yaml
settings:
  alert_webhook: "https://ntfy.sh/your-topic"   # أو Slack / Discord / Telegram Bot API
  alerts_enabled: true
  failure_threshold: 2                          # عدد الإخفاقات قبل إعلان الحادثة
```

## الجدولة المجانية عبر GitHub Actions

الملف `.github/workflows/monitor.yml` يشغّل فحصًا كل 15 دقيقة على مستودع عام (مجاني)،
ويفشل الـ job عند توقف هدف — فتصلك رسالة بريد تلقائية من GitHub. أضف في
`Settings → Secrets` المتغير `ADLOAB_EXTRA_DOMAINS` بنطاقك إن أردت عدم تخزينه في الملف.

## بنية المشروع

```
app/
  config.py      الإعدادات + حاجز الملكية (Ownership Guard)
  db.py          SQLite: فحوصات، إحصاءات، حوادث
  checker.py     محرّك الفحص: DNS/TLS/TTFB + فحص المتصفح + التحقق من المحتوى
  scheduler.py   مجدول غير متزامن + إدارة الحوادث
  alerts.py      سجل + Webhook
  main.py        واجهة FastAPI + API
  cli.py         سطر الأوامر
  static/        لوحة تحكم عربية RTL بلا أي مكتبة خارجية
config/          owned_domains.yaml (الملكية) + targets.yaml (الأهداف)
tests/           اختبارات pytest (حاجز الملكية، الإحصاءات، دورة الحادثة)
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

## الاختبارات

```bash
pip install pytest
pytest -q
```

---

## استغلال GitHub Student Pack بشكل مشروع

| الأداة | الاستخدام المشروع في هذا المشروع |
|---|---|
| **GitHub Actions** | جدولة الفحوصات مجانًا + CI للاختبارات |
| **BrowserStack** (ساعات مجانية للطلاب) | تشغيل `tests/e2e` لموقعك على متصفحات وأجهزة حقيقية |
| **DigitalOcean / Heroku** أرصدة | استضافة اللوحة 24/7 بدل تشغيلها محليًا |
| **Namecheap / .me** | نطاق لمشروعك + شهادة SSL لاختبار المراقبة |
| **Copilot / JetBrains** | تطوير المشروع نفسه |

مثال تشغيل على BrowserStack من GitHub Actions (لموقعك فقط):

```yaml
- name: BrowserStack smoke test
  env:
    BROWSERSTACK_USERNAME: ${{ secrets.BROWSERSTACK_USERNAME }}
    BROWSERSTACK_ACCESS_KEY: ${{ secrets.BROWSERSTACK_ACCESS_KEY }}
  run: npx browserstack-cypress run --spec "cypress/e2e/smoke.cy.js"
```

## الترخيص

MIT — استخدمه، طوّره، وشاركه.
