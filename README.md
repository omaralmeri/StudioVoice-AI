# 🎙️ StudioVoice-AI | استوديو هندسة وتنقية الصوت بالذكاء الاصطناعي

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/omaralmeri/StudioVoice-AI/blob/main/StudioVoice.ipynb)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange)
![Gradio](https://img.shields.io/badge/UI-Gradio-red)

نظام متكامل لمعالجة وهندسة الصوتيات بالذكاء الاصطناعي، يتيح عزل الضوضاء وتحويل التسجيلات العادية إلى خامة صوت استوديو احترافية، مع ميزة استخراج الصوت فائق السرعة من مقاطع الفيديو.

---

## ✨ المميزات الرئيسية (Key Features)

1. **خامة صوت استوديو (Studio Voice Synthesis):**
   - إعادة توليد الترددات المفقودة وإعطاء الصوت دفئاً وعمقاً مشابهاً لمايكروفونات الاستوديو.
   - عزل ضجيج المكيفات وصدى الغرفة والتشويش المرتفع.
2. **ماسترينج صوتي احترافي (Broadcast Mastering):**
   - ضبط مستوى العلو القياسي للبث (-14 LUFS) المتوافق مع معايير YouTube و Spotify.
   - فلتر عزل الاهتزازات الرخيمة غير المسموعة (High-Pass Filter at 30Hz).
3. **تسجيل مايكروفون مباشر (Live Mic Recording):**
   - تسجيل فوري من المتصفح ومعالجة الصوت بنقرة واحدة.
4. **استخراج سريع للصوت (Instant Audio Extract):**
   - سحب مسار الصوت من أي مقطع فيديو (MP4, MKV, MOV) في أقل من ثانية وبجودة خام غير مضغوطة (WAV) أو MP3.
5. **إعادة دمج الفيديو التلقائية (Lossless Video Remuxing):**
   - دمج الصوت النقي داخل الفيديو الأصلي بدون إعادة ضغط الصورة وبمزامنة تامة لحركة الشفاه.

---

## 🚀 طريقة التشغيل السريعة (Quick Start via Colab)

يمكنك تشغيل المنظومة مباشرة دون الحاجة لتثبيت أي متطلبات على جهازك بالضغط على الزر أدناه:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/omaralmeri/StudioVoice-AI/blob/main/StudioVoice.ipynb)

---

## 🛠️ المتطلبات البرمجية والتشغيل المحلي (Local Setup)

1. **استنساخ المستودع:**
   ```bash
   git clone [https://github.com/omaralmeri/StudioVoice-AI.git](https://github.com/omaralmeri/StudioVoice-AI.git)
   cd StudioVoice-AI
