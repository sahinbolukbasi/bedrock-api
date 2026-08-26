# Enterprise LLM Chat, Canvas & Dynamic Artifacts Mimarisi ve Teknik Şartnamesi
**Standartlar:** OpenWebUI, Claude 3.5 Artifacts, OpenUI & Vercel AI SDK

---

## 1. Yönetici Özeti & Mimari Felsefe

Bu şartname; Amazon Bedrock ve Anthropic Claude altyapısı üzerinde çalışan, **OpenWebUI**, **Claude Artifacts** ve **OpenUI** standartlarında, kurumsal seviyede (Enterprise-Grade) bir **LLM Chat & Canvas Etkileşim Platformu** inşa etmek için hazırlanmıştır.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               ENTERPRISE LLM WORKSPACE                                 │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│        SOHBET & THREAD AKIŞI (60%)     │        DYNAMIC ARTIFACTS CANVAS (40%)         │
│ ┌────────────────────────────────────┐ │ ┌───────────────────────────────────────────┐ │
│ │ 🤖 Model: Claude 3.5 Sonnet        │ │ │ 🎨 Live Preview / Code / Diagram / Canvas │ │
│ │ 🧠 <think> Reasoning Accordion     │ │ │ ───────────────────────────────────────── │ │
│ │ 📝 Streaming Markdown Output       │ │ │  • Sandboxed HTML/JS/Tailwind Renderer   │ │
│ │ ◀ 2/3 ▶ Version Branching Toolbar  │ │ │  • Interactive Mermaid.js Flowcharts      │ │
│ └────────────────────────────────────┘ │ │  • Editable Dynamic JSON Forms (OpenUI)  │ │
│ ┌────────────────────────────────────┐ │ │  • Download / Fullscreen / Copy Code     │ │
│ │ ⌨️ @Model /Slash Multimodal Input  │ │ └───────────────────────────────────────────┘ │
│ └────────────────────────────────────┘ │                                               │
└────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 2. Modül 1: İleri Seviye Giriş Alanı (Chat Input UX Engine)

### 2.1 Çok Modlu Giriş & Sürükle-Bırak (Multimodal Input & Drag-Drop)
* **Desteklenen Formatlar:** PDF dokümanları, CSV/Excel tabloları, Kod dosyaları (`.py`, `.ts`, `.json`, `.sql`) ve Görseller (`PNG`, `JPEG`, `WEBP`).
* **Sürükle-Bırak Katmanı:** Giriş kutusu veya tüm ekran üzerine dosya sürüklendiğinde beliren cam efektli (glassmorphism) drop-zone.
* **Token ve Boyut Önizlemesi:** Yüklenen dosyalar küçük çipler (chips) halinde gösterilir. Görseller için minyatür önizleme, PDF/kod dosyaları için tahmini token sayacı ve silme (`X`) butonu bulunur.
* **Sesli Giriş (Web Audio API / MediaRecorder):** Tarayıcı mikrofonu ile canlı ses kaydı, dalga formu (waveform) animasyonu ve Speech-to-Text (Whisper/Transcribe) entegrasyonu.

### 2.2 Komut & Etiket Sistemi (@ Mentions & / Slash Commands)
* **`@` Mentions Popover:**
  * `@claude-3-5-sonnet`, `@amazon-nova-pro`, `@llama-3-70b` gibi modeller arasında konuşma ortasında anlık geçiş.
  * `@docs/aws-architecture.pdf` veya `@knowledge/sales-data` ile vektör veritabanından bağlam (RAG) enjeksiyonu.
* **`/` Slash Komutları:**
  * `/summarize`: Mevcut metni özetleme şablonunu tetikler.
  * `/code`: Kod üretici asistan modunu aktifleştirir.
  * `/canvas`: Doğrudan canvas artifact üretim moduna geçer.
  * `/clear`: Sohbet bağlamını sıfırlar.

### 2.3 Girdi Durumu & Yaşam Döngüsü (Input Lifecycle)
* **Auto-resize Textarea:** İçerik uzadıkça 1 satırdan maksimum 8 satıra (max-h-48) kadar otomatik büyüyen, sonrasında dikey kaydırma çubuğu açan yapı.
* **Stream Durdurma (Stop Generating):** İstek atıldığı anda `AbortController.abort()` mekanizması tetiklenebilir bir **"Durdur" (Stop)** butonuna dönüşür.
* **Yeniden Deneme & Model Çatallama:** Aynı promptu farklı bir modelle (örn: Nova Pro vs Claude 3.5) yeniden üretme seçeneği.

---

## 3. Modül 2: Yanıt Akışı, Render & Canvas Artifacts

### 3.1 Zengin Markdown & Kod Blokları (Rich Code Highlighting)
* **Sözdizimi Vurgulama:** `PrismJS` / `highlight.js` ile 50+ programlama dili desteği ve otomatik dil tespiti.
* **Satır Numaraları & Collapsible Bloklar:** 25 satırı aşan kod parçaları için "Genişlet / Daralt" seçeneği.
* **Kod Aksiyon Barı:** Dil etiketi, dosya adı, tek tıkla panoya kopyalama ve *"Canvas'ta Aç"* butonu.

### 3.2 Dynamic Artifacts / Canvas (OpenUI & Claude Standard)
Model çıktısı bir kod dosyası, görsel arayüz, SVG veya diyagram ürettiğinde sohbet ekranı bölünür (**Split View 60/40**):

| Artifact Türü | Render Motoru | Etkileşim Yeteneği |
| :--- | :--- | :--- |
| **HTML / Tailwind / JS** | Sandboxed `<iframe>` (`allow-scripts`) | Canlı çalışan web bileşeni ve interaktif butonlar |
| **Mermaid.js Diyagramları** | `@mermaid-js/mermaid` | Mimari şemalar, akış diyagramları, SVG olarak dışa aktarma |
| **Chart.js / Recharts** | Canvas/SVG Grafikleri | Dinamik finansal ve analitik veri grafikleri |
| **OpenUI JSON Formları** | Schema-Driven Form Renderer | Kullanıcıdan veri toplayan dinamik input formları |
| **Kod Dosyaları** | Monaco Editor / CodeViewer | Dosya indirme (`.tsx`, `.py`), düzenleme ve kopyalama |

### 3.3 Akıl Yürütme İzleri (<think> Reasoning Traces)
* DeepSeek R1, Nova ve Claude modellerinden gelen `<think>...</think>` blokları ana metinden ayrıştırılır.
* Kullanıcının dikkatini dağıtmayacak şekilde **"Düşünce Sürecini İncele (X saniye)"** başlıklı modern bir akordeon (accordion) kartı içine alınır.

### 3.4 Mesaj Üstü Aksiyonlar (Action Toolbar)
* **Kopyala & Markdown Al:** Ham markdown veya zengin metin kopyalama.
* **Metin Seslendirme (TTS / Web Speech API):** Yanıtı doğal ses tonuyla dinleme.
* **Mesaj Düzenleme & Dallanma (Forking):** Kullanıcı eski mesajını düzenlediğinde önceki varyasyonları silmeden yeni bir dal oluşturma.
* **Beğeni & Geri Bildirim:** 👍 / 👎 değerlendirmesi ile model çıktılarının kalite takibi.

---

## 4. Modül 3: Bağlam, Bellek & Thread Ağacı (Tree Architecture)

### 4.1 Mesaj Ağacı Veri Modeli (Branching Tree Schema)
Mesajlar doğrusal bir liste yerine ebeveyn-çocuk ilişkisiyle modellenir:

```typescript
export interface ChatMessageNode {
  id: string;                    // UUID
  parent_id: string | null;      // Önceki mesaj ID'si
  children_ids: string[];        // Bu mesajdan dallanan yanıtlar
  role: "user" | "assistant" | "system";
  content: string;
  reasoning_content?: string;    // <think> blokları
  artifacts?: ArtifactPayload[]; // Canvas çıktıları
  model?: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    cost_usd: number;
  };
  created_at: string;
}
```

### 4.2 Navigasyon Varyasyonları (1/3 Branch Switcher)
Bir kullanıcı mesajı düzenlendiğinde:
* Arayüzde `◀ 2/3 ▶` şeklinde varyasyon butonları belirir.
* Kullanıcı dilediği varyasyona tıkladığında tüm alt konuşma ağacı o varyasyonun izlediği yola göre anında yeniden oluşturulur.

### 4.3 Model Hiperparametre Dock'u & Maliyet Sayacı
* **Sıcaklık (Temperature):** 0.0 (Mantıksal / Kod) - 1.0 (Yaratıcı / Yazarlık) slider kontrolü.
* **Top-P & Max Tokens:** Hassas üretim parametreleri.
* **Sistem Talimatı (System Prompt):** "Sen kıdemli bir AWS mimarısın..." şeklinde dinamik persona atama.
* **Maliyet & Token Sayacı:** Her mesajın altında harcanan token ve `0.0012 USD` gibi hesaplanan anlık maliyet göstergesi.

### 4.4 Oturum & Dışa Aktarma Yönetimi
* **Otomatik Başlıklandırma:** İlk 2 mesajdan sonra LLM ile otomatik kısa ve anlamlı başlık oluşturma.
* **Klasörleme & Etiketler:** "İş", "Kodlama", "Finans" şeklinde etiketleme ve arama.
* **Dışa Aktarma:** `Markdown (.md)`, `JSON Tree (.json)`, `PDF` ve `CSV`.

---

## 5. Frontend & Sandbox Güvenlik Mimarisi

```
                               ┌───────────────────────────────────┐
                               │       Next.js Chat Host (App)     │
                               └─────────────────┬─────────────────┘
                                                 │ postMessage()
                                                 ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                      SANDBOXED CANVAS RUNTIME (iframe)                            │
│  Attributes: sandbox="allow-scripts allow-popups"                                 │
│  • DOMPurify HTML Sanitization                                                    │
│  • Tailwind CSS Injected via CDN                                                  │
│  • React 18 Standalone UMD Runner / Babel Standalone                              │
│  • Mermaid.js v10 SVG Parser                                                      │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Adım Adım Kodlama & Uygulama Yol Haritası

| Aşama | Modül | Hedeflenen Çıktı |
| :--- | :--- | :--- |
| **Faz 1** | **Giriş & Mention UX** | Auto-resize textarea, `@` model seçici, `/` hızlı komut popover ve dosya/görsel sürükle-bırak motoru. |
| **Faz 2** | **Artifacts & Split Canvas** | Claude tarzı sağ panel Canvas arayüzü, sandboxed HTML/SVG/Mermaid render motoru ve kopyalama araçları. |
| **Faz 3** | **Branching & Versioning** | Mesaj ağacı veri modeli (`parent_id`/`children_ids`), `1/3` varyasyon seçici ve mesaj düzenleme motoru. |
| **Faz 4** | **Reasoning & Gelişmiş Render** | `<think>` akıl yürütme akordeonu, PrismJS kod blokları, TTS seslendirme ve token/maliyet sayaçları. |
