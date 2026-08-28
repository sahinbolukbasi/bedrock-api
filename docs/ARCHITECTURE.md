# 🏛️ Sistem & Bulut Mimarisi (End-to-End System Architecture)

Bu doküman; **AWS Bedrock AI Gateway**, **Otonom Agent Motoru** ve **AWS Bulut Altyapısı**'nın uçtan uca teknik mimarisini, veri akışını, ağ topolojisini ve güvenlik sınırlarını detaylandırmaktadır.

---

## ☁️ 1. AWS Bulut Altyapı Topolojisi (VPC & Container Architecture)

```mermaid
flowchart TD
    subgraph InternetLayer [Genel İnternet & İstemciler]
        WebUsers[💻 Web Kullanıcıları]
        TelegramClients[📱 Telegram Kullanıcıları]
        APICallers[🔌 REST API & SDK İstemcileri]
    end

    subgraph AWSVPC [AWS Production VPC - us-east-1]
        subgraph PublicSubnets [Public Subnets - Multi-AZ]
            ALB["AWS Application Load Balancer (ALB)<br/>bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com<br/>• Port 80/443: Web & API<br/>• Port 3001: Grafana Canlı İzleme"]
        end

        subgraph PrivateAppSubnets [Private App Subnets - ECS Fargate Kümesi]
            FrontendSvc["🎨 Frontend Service (Port: 3000)<br/>Next.js 14 App Router"]
            BackendSvc["⚙️ Backend Service (Port: 8000)<br/>FastAPI Asenkron Motoru + RAG"]
            TelegramSvc["📱 Telegram Worker Service<br/>Stateful Polling Engine"]
            MonitoringSvc["📊 Monitoring Service (Port: 3000 / 9090)<br/>Grafana 10.4 + Prometheus"]
        end

        subgraph PrivateDataSubnets [Private Isolated Data Subnets]
            RDSPostgres["🗄️ AWS RDS PostgreSQL 16 (Multi-AZ)<br/>bedrock-gateway-db.cobqqmqcs7xh.us-east-1.rds.amazonaws.com:5432"]
            RedisCluster["⚡ AWS ElastiCache Redis Cluster<br/>bedrock-gateway-redis.hmoplf.0001.use1.cache.amazonaws.com:6379"]
        end
    end

    subgraph AWSSaaS [AWS Yönetilen Bulut & Güvenlik Servisleri]
        BedrockService["🧠 AWS Bedrock Foundation Models<br/>• Claude 3.7 Sonnet, Claude 3.5 Haiku<br/>• Amazon Nova Micro, Titan Embeddings"]
        GuardrailsService["🛡️ AWS Bedrock Guardrails<br/>PII Maskeleme & Prompt Injection Koruması"]
        SecretsMgr["🔐 AWS Secrets Manager<br/>bedrock-gateway-secrets-prod"]
        S3Corpus["📦 Amazon S3 Bucket<br/>bedrock-gateway-artifacts-prod"]
        CloudWatchLogs["📝 Amazon CloudWatch Logs<br/>/ecs/bedrock-gateway"]
    end

    InternetLayer --> ALB
    ALB -->|/ & UI Sayfaları| FrontendSvc
    ALB -->|/api/* , /v1/* , /docs| BackendSvc
    ALB -->|:3001 İzleme| MonitoringSvc
    TelegramClients <--> TelegramSvc

    FrontendSvc <--> BackendSvc
    TelegramSvc <--> BackendSvc
    BackendSvc <--> RDSPostgres
    BackendSvc <--> RedisCluster
    BackendSvc <--> S3Corpus
    BackendSvc <--> SecretsMgr
    BackendSvc <--> GuardrailsService
    GuardrailsService <--> BedrockService

    MonitoringSvc -->|Scrapes /metrics| BackendSvc
    PrivateAppSubnets --> CloudWatchLogs
```

---

## 🤖 2. 10 Temel Mimari Bileşenli Otonom Agent Motoru

Platform, otonom yapay zeka ajanlarını 10 modüler bileşen üzerinden yönetir:

### 2.1. Kimlik ve Persona Tanımı (`goal_definition`)
- Her agent için **Rol**, **Hedef Tanımı (`goal_definition`)**, **İletişim Tonu** ve **Sınırları** açıkça yapılandırılır. Model, her göreve bu kimlik çerçevesinde başlar.

### 2.2. 3-Katmanlı Hafıza Motoru (`memory_engine.py` & `semantic_memory.py`)
- **Katman 1 (Kısa Süreli Hafıza):** Son 6 mesaj tam metin tutulur; eski mesajlar tek bir arka plan paragrafına sıkıştırılır (**%75+ token tasarrufu**).
- **Katman 2 (Uzun Süreli Hafıza / Mem0 Standardı):** Kullanıcının tercihleri, uzmanlık alanı, dili ve kuralları yapılandırılmış `SemanticMemoryFact` grafında saklanır. Soruyla ilgili maddeler semantik benzerlikle çekilir.
- **Katman 3 (Çalışma Hafızası / Scratchpad):** Çok adımlı ReAct görevlerinde ara bulgular saklanır.

### 2.3. Native AWS Bedrock Converse API Tool Calling (`bedrock_tools.py`)
- Regex metin taklidi yerine AWS Bedrock'un resmi **`toolConfig`** standardı kullanılır:
  - `web_search`: DuckDuckGo canlı internet ve haber taraması.
  - `python_interpreter`: İzolasyonlu stdout/globals sandbox ortamında güvenli Python kod çalıştırma.
  - `finance_market_data`: Anlık borsa, kripto ve döviz kurları.
  - `schedule_reminder`: Zamanlayıcı ve alarmlar.

### 2.4. ReAct Muhakeme & Öz-Değerlendirme (Self-Reflection)
- Model `Thought ➔ Action ➔ Observation ➔ Reflection (Öz-Değerlendirme)` adımlarını izler. Araçtan gelen veriyi hedefe göre denetler; eksikse ek arama yapar, tamamsa nihai cevabı üretir.

### 2.5. Otonomi Düzeyleri (Human-in-the-Loop)
- **`AUTONOMOUS`:** Görevi baştan sona kendi başına tamamlar.
- **`CONFIRMATION_REQUIRED`:** Kritik eylemlerde kullanıcı onayı ister.
- **`ADVISORY`:** Yalnızca tavsiye ve bilgi sunar.

### 2.6. Maliyetsiz Yerel Vektör RAG (`local_rag.py`)
- Harici pahalı vektör veritabanı gerektirmeden kullanıcı tarafından verilen Website URL'leri veya dokümanlar 450 karakterlik parçalara (overlapping chunks) bölünür; BM25 ve Cosine benzerlik algoritmasıyla sadece en alakalı parçalar prompt'a enjekte edilir.

### 2.7. AWS Bedrock Guardrails & Güvenlik (`guardrails.py`)
- Kredi kartı, telefon ve e-posta numaraları için **PII Maskeleme (Anonymization)**.
- Sistem talimatlarını aşmaya yönelik **Prompt Injection & Jailbreak Koruması**.

### 2.8. Stateful Model Context Protocol (MCP) Server (`mcp_server.py`)
- Standart MCP protokolü ile oturumlar arası bağlam saklama ve dinamik araç çalıştırma yeteneği.

### 2.9. Yaşayan & Büyüyen Ajan (Living Agent IQ - `agent_growth.py`)
- Botlar **🌱 Yenidoğan (Lv 1) ➔ 🌿 Çırak (Lv 2) ➔ 🎓 Uzman (Lv 3) ➔ 👑 Üstat (Lv 4)** seviyelerine yükselir.
- Görev tamamlama (+20 XP), canlı veri işleme (+30 XP) ve kullanıcı beğenileriyle (+50 XP) dinamik IQ puanı artar.

### 2.10. Çok Kanallı İletişim (Web Studio & Telegram Bot)
- Frontier Web Studio ve Telegram Asistan Botu (`@BedrocksAiBot`) aynı hafıza ve model havuzunu paylaşır.
