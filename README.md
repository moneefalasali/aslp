# منصة التعلم الذكي - Smart Learning System

منصة تعليمية متقدمة تستخدم الذكاء الاصطناعي لتحويل المحتوى التعليمي (ملفات PDF وتسجيلات صوتية) إلى ملخصات وأسئلة اختبار تفاعلية.

## المميزات الرئيسية

✨ **تحليل ذكي للملفات**: استخراج ملخصات وأسئلة اختبار تلقائية من ملفات PDF والملفات الصوتية.

🎤 **تحويل الصوت إلى نص**: تحويل التسجيلات الصوتية إلى نصوص مكتوبة باستخدام OpenAI Whisper.

📊 **إحصائيات وتقارير**: عرض نتائج التحليل مع حساب درجات الاختبارات.

👥 **نظام إدارة المستخدمين**: تسجيل دخول وإدارة حسابات المستخدمين والمسؤولين.

☁️ **تخزين سحابي آمن**: تخزين الملفات في Wasabi S3 مع الحفاظ على الخصوصية.

🔐 **نظام مصادقة آمن**: استخدام JWT للتحقق من هوية المستخدمين.

---

## المتطلبات التقنية

- **Python**: 3.10 أو أحدث
- **قاعدة بيانات**: SQLite (افتراضي) أو PostgreSQL (للإنتاج)
- **خدمات خارجية**:
  - OpenAI API (للتحليل وتحويل الصوت)
  - Wasabi S3 (لتخزين الملفات)

---

## التثبيت والإعداد

### 1. استنساخ المشروع أو فك ضغطه

```bash
unzip smart-learning-full-system.zip
cd smart-learning
```

### 2. تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

### 3. إعداد ملف البيئة

```bash
# انسخ ملف المثال
cp .env.example .env

# قم بتحرير الملف وأضف بيانات اعتمادك
nano .env
```

**المتغيرات المهمة التي يجب تعديلها:**

| المتغير | الوصف | مثال |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | مفتاح OpenAI API | `sk-...` |
| `WASABI_ACCESS_KEY` | مفتاح الوصول إلى Wasabi | `XXXXXX` |
| `WASABI_SECRET_KEY` | المفتاح السري لـ Wasabi | `XXXXXX` |
| `WASABI_BUCKET_NAME` | اسم الـ Bucket | `my-bucket` |
| `SECRET_KEY` | مفتاح سري لتشفير التوكنات | `your-secret-key` |

### 4. تشغيل التطبيق

```bash
python app.py
```

سيعمل التطبيق على: `http://localhost:8000`

---

## هيكل المشروع

```
smart-learning/
├── app.py                    # نقطة الدخول الرئيسية
├── config.py                 # إعدادات التطبيق
├── database.py               # إعداد قاعدة البيانات
├── models.py                 # نماذج قاعدة البيانات
├── schemas.py                # نماذج التحقق من البيانات (Pydantic)
├── requirements.txt          # المكتبات المطلوبة
├── .env                      # متغيرات البيئة (لا تنسخ إلى Git)
├── .env.example              # مثال على متغيرات البيئة
│
├── routes/                   # مسارات API
│   ├── auth.py              # مسارات المصادقة
│   ├── admin.py             # مسارات الإدارة
│   └── main_routes.py       # المسارات الرئيسية
│
├── services/                 # خدمات التطبيق
│   ├── auth_service.py      # خدمات المصادقة والتوكنات
│   ├── user_service.py      # خدمات إدارة المستخدمين
│   ├── ai_service.py        # خدمات الذكاء الاصطناعي
│   ├── pdf_service.py       # خدمات معالجة PDF
│   ├── audio_service.py     # خدمات معالجة الصوت
│   └── storage_service.py   # خدمات التخزين السحابي
│
├── templates/                # صفحات HTML
│   ├── index.html           # الصفحة الرئيسية
│   ├── login.html           # صفحة تسجيل الدخول
│   ├── register.html        # صفحة التسجيل
│   ├── admin_login.html     # صفحة دخول الإدارة
│   └── admin_dashboard.html # لوحة تحكم الإدارة
│
└── static/                   # الملفات الثابتة
    ├── css/
    │   └── style.css        # أنماط CSS
    └── js/
        └── main.js          # سكريبت JavaScript الرئيسي
```

---

## مسارات API

### المصادقة (`/api/auth`)

| الطريقة | المسار | الوصف |
| :--- | :--- | :--- |
| POST | `/register` | تسجيل مستخدم جديد |
| POST | `/login` | تسجيل الدخول |
| POST | `/refresh` | تحديث التوكن |
| GET | `/me` | الحصول على بيانات المستخدم الحالي |
| POST | `/admin/register` | تسجيل مسؤول جديد |
| POST | `/admin/login` | تسجيل دخول المسؤول |

### المعالجة (`/api`)

| الطريقة | المسار | الوصف |
| :--- | :--- | :--- |
| POST | `/upload` | رفع ملف PDF أو صوتي |
| POST | `/process-pdf` | استخراج نصوص من PDF |
| POST | `/process-audio` | تحويل الصوت إلى نص |
| POST | `/analyze` | تحليل النص بالذكاء الاصطناعي |
| GET | `/results/<file_id>` | الحصول على نتائج التحليل |
| GET | `/history` | الحصول على سجل التحليلات (يتطلب مصادقة) |

### الإدارة (`/api/admin`)

| الطريقة | المسار | الوصف |
| :--- | :--- | :--- |
| GET | `/users` | الحصول على قائمة المستخدمين |
| DELETE | `/users/<user_id>` | حذف مستخدم |
| GET | `/statistics` | الحصول على إحصائيات النظام |
| GET | `/health` | التحقق من صحة النظام |

---

## أمثلة على الاستخدام

### تسجيل مستخدم جديد

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "أحمد محمد",
    "username": "ahmed_m",
    "email": "ahmed@example.com",
    "password": "password123"
  }'
```

### تسجيل الدخول

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ahmed_m",
    "password": "password123"
  }'
```

### رفع ملف

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"
```

### تحليل النص

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "نص المحتوى هنا...",
    "file_id": "file-id-here",
    "file_name": "document.pdf",
    "file_type": "pdf"
  }'
```

---

## الإصلاحات التي تم إجراؤها

✅ **إضافة ديكوريتور `token_required`**: لحماية المسارات التي تتطلب مصادقة.

✅ **إصلاح مسارات الاستيراد**: تصحيح استيراد `auth_service` في `user_service.py`.

✅ **إضافة ملف `.env`**: لإدارة آمنة لمتغيرات البيئة.

✅ **التحقق من التوافق**: التأكد من توافق جميع الواجهات الأمامية مع API.

---

## نصائح الأمان

🔒 **لا تنشر مفاتيحك**: لا تضع مفاتيح API الحقيقية في الكود، استخدم ملف `.env`.

🔒 **غيّر `SECRET_KEY`**: غيّر قيمة `SECRET_KEY` في الإنتاج.

🔒 **استخدم HTTPS**: في الإنتاج، استخدم HTTPS بدلاً من HTTP.

🔒 **حدّث المكتبات**: قم بتحديث المكتبات بانتظام للحصول على آخر تصحيحات الأمان.

---

## استكشاف الأخطاء

### خطأ: `ModuleNotFoundError`

**الحل**: تأكد من تثبيت جميع المكتبات:
```bash
pip install -r requirements.txt
```

### خطأ: `OPENAI_API_KEY not found`

**الحل**: تأكد من ملء `OPENAI_API_KEY` في ملف `.env`.

### خطأ: `Database connection failed`

**الحل**: تأكد من أن قاعدة البيانات قابلة للوصول أو غيّر `DATABASE_URL` في `.env`.

---

## الدعم والمساهمة

للأسئلة أو الإبلاغ عن الأخطاء، يرجى فتح issue أو التواصل مع فريق التطوير.

---

## الترخيص

هذا المشروع مرخص تحت MIT License.
