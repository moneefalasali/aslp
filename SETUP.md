# دليل الإعداد التفصيلي - Smart Learning System

هذا الدليل يشرح خطوة بخطوة كيفية إعداد وتشغيل منصة التعلم الذكي.

---

## الخطوة 1: المتطلبات الأساسية

تأكد من أن لديك:
- **Python 3.10+** مثبت على جهازك
- **pip** (مدير حزم Python)
- **Git** (اختياري، لاستنساخ المشروع)

للتحقق من إصدار Python:
```bash
python --version
```

---

## الخطوة 2: استخراج المشروع

إذا كان المشروع مضغوطاً:

```bash
unzip smart-learning-full-system.zip
cd smart-learning
```

أو إذا كنت تستخدم Git:

```bash
git clone <repository-url>
cd smart-learning
```

---

## الخطوة 3: إنشاء بيئة افتراضية (Virtual Environment)

من المفضل استخدام بيئة افتراضية لعزل المشروع:

```bash
# إنشاء البيئة الافتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
# على Windows:
venv\Scripts\activate

# على macOS/Linux:
source venv/bin/activate
```

---

## الخطوة 4: تثبيت المكتبات

```bash
pip install -r requirements.txt
```

هذا سيثبت جميع المكتبات المطلوبة:
- Flask و Flask-CORS
- SQLAlchemy (قاعدة البيانات)
- OpenAI (للذكاء الاصطناعي)
- Boto3 (لـ Wasabi S3)
- PyPDF2 (معالجة PDF)
- وغيرها...

---

## الخطوة 5: إعداد ملف البيئة

### 5.1 نسخ ملف المثال

```bash
cp .env.example .env
```

### 5.2 تحرير ملف `.env`

افتح الملف بمحرر نصوص وأضف بيانات اعتمادك:

```bash
nano .env
# أو استخدم محرر آخر مثل VS Code
```

### 5.3 ملء البيانات المطلوبة

#### أ. OpenAI API

1. اذهب إلى [OpenAI Platform](https://platform.openai.com/)
2. سجل الدخول أو أنشئ حساباً
3. انتقل إلى [API Keys](https://platform.openai.com/api-keys)
4. انقر على "Create new secret key"
5. انسخ المفتاح والصقه في `.env`:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxx
```

#### ب. Wasabi S3 Storage

1. اذهب إلى [Wasabi](https://wasabisys.com/)
2. أنشئ حساباً أو سجل الدخول
3. انتقل إلى Access Keys
4. أنشئ مفتاح وصول جديد
5. انسخ البيانات إلى `.env`:

```env
WASABI_ACCESS_KEY=your-access-key
WASABI_SECRET_KEY=your-secret-key
WASABI_BUCKET_NAME=your-bucket-name
WASABI_REGION=us-east-1
```

**ملاحظة**: تأكد من إنشاء Bucket جديد في Wasabi قبل تشغيل التطبيق.

#### ج. المتغيرات الأخرى

```env
# مفتاح سري قوي (غيّره في الإنتاج)
SECRET_KEY=your-super-secret-key-change-in-production

# بيانات المسؤول الافتراضي
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@smartlearning.com

# إعدادات أخرى
DEBUG=False
DATABASE_URL=sqlite:///./smart_learning.db
```

---

## الخطوة 6: تشغيل التطبيق

### 6.1 تشغيل الخادم

```bash
python app.py
```

ستظهر رسالة مشابهة لهذه:

```
 * Running on http://127.0.0.1:8000
 * Press CTRL+C to quit
```

### 6.2 الوصول إلى التطبيق

افتح متصفحك وانتقل إلى:
```
http://localhost:8000
```

---

## الخطوة 7: اختبار التطبيق

### 7.1 اختبار الصحة

```bash
curl http://localhost:8000/health
```

يجب أن تحصل على:
```json
{"status":"healthy","version":"1.0.0"}
```

### 7.2 تسجيل مستخدم جديد

1. انتقل إلى صفحة التسجيل: `http://localhost:8000/register`
2. أدخل البيانات المطلوبة
3. انقر على "تسجيل"

### 7.3 تسجيل الدخول

1. انتقل إلى صفحة تسجيل الدخول: `http://localhost:8000/login`
2. أدخل بيانات المستخدم
3. انقر على "دخول"

### 7.4 رفع ملف واختباره

1. انتقل إلى صفحة الرفع
2. اختر ملف PDF أو صوتي
3. انقر على "رفع ومعالجة"
4. انتظر النتائج

---

## الخطوة 8: تسجيل دخول الإدارة

### 8.1 الوصول إلى لوحة الإدارة

انتقل إلى: `http://localhost:8000/admin-login`

### 8.2 بيانات المسؤول الافتراضية

```
اسم المستخدم: admin
كلمة المرور: admin123
```

**تحذير**: غيّر كلمة المرور الافتراضية فوراً في الإنتاج!

---

## استكشاف الأخطاء الشائعة

### ❌ خطأ: `ModuleNotFoundError: No module named 'flask'`

**السبب**: لم يتم تثبيت المكتبات.

**الحل**:
```bash
pip install -r requirements.txt
```

---

### ❌ خطأ: `OPENAI_API_KEY not found`

**السبب**: لم يتم تعيين مفتاح OpenAI في `.env`.

**الحل**:
1. تأكد من وجود ملف `.env`
2. أضف `OPENAI_API_KEY` مع قيمة صحيحة
3. أعد تشغيل التطبيق

---

### ❌ خطأ: `Connection to Wasabi failed`

**السبب**: بيانات Wasabi غير صحيحة أو الـ Bucket غير موجود.

**الحل**:
1. تحقق من صحة `WASABI_ACCESS_KEY` و `WASABI_SECRET_KEY`
2. تأكد من وجود الـ Bucket
3. تحقق من اسم الـ Bucket في `.env`

---

### ❌ خطأ: `Database is locked`

**السبب**: قد يكون هناك عملية أخرى تستخدم قاعدة البيانات.

**الحل**:
```bash
# احذف ملف قاعدة البيانات وأعد التشغيل
rm smart_learning.db
python app.py
```

---

## الخطوة 9: التشغيل في الإنتاج

### 9.1 استخدام Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 9.2 استخدام Docker (اختياري)

إنشاء `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

بناء الصورة:
```bash
docker build -t smart-learning .
```

تشغيل الحاوية:
```bash
docker run -p 8000:8000 --env-file .env smart-learning
```

---

## الخطوة 10: إعدادات الأمان

### 10.1 تغيير `SECRET_KEY`

في الإنتاج، استخدم مفتاح قوي:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

انسخ الناتج إلى `SECRET_KEY` في `.env`.

### 10.2 تفعيل HTTPS

استخدم خادم ويب مثل Nginx أو Apache مع شهادة SSL.

### 10.3 تحديث قاعدة البيانات

للإنتاج، استخدم PostgreSQL بدلاً من SQLite:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/smart_learning
```

---

## معلومات إضافية

### الملفات المهمة

| الملف | الوصف |
| :--- | :--- |
| `.env` | متغيرات البيئة (لا تنسخ إلى Git) |
| `requirements.txt` | المكتبات المطلوبة |
| `app.py` | نقطة الدخول الرئيسية |
| `config.py` | إعدادات التطبيق |

### المجلدات الرئيسية

| المجلد | الوصف |
| :--- | :--- |
| `routes/` | مسارات API |
| `services/` | خدمات التطبيق |
| `templates/` | صفحات HTML |
| `static/` | ملفات CSS و JavaScript |

---

## الخطوات التالية

1. اقرأ `README.md` لفهم هيكل المشروع
2. اطلع على `smart-learning-guide.md` لشرح الميزات
3. استكشف مسارات API في `routes/`
4. قم بتخصيص التطبيق حسب احتياجاتك

---

## الدعم

إذا واجهت مشاكل:
1. تحقق من رسائل الخطأ بعناية
2. راجع قسم "استكشاف الأخطاء"
3. تأكد من تثبيت جميع المكتبات
4. تحقق من متغيرات البيئة

---

**تم إعداد هذا الدليل بنجاح! استمتع بمنصة التعلم الذكي.**
