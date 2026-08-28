# 🏛️ Sistem & Bulut Ağ Mimarisi (End-to-End System & Network Architecture)

Bu doküman; **AWS Bedrock AI Gateway**, **Otonom Agent Motoru** ve **AWS Bulut Altyapısı**'nın uçtan uca teknik mimarisini, veri akışını, ağ topolojisini, güvenlik sınırlarını ve iç ağ haberleşme matrisini detaylandırmaktadır.

---

## 🌐 1. AWS Bulut Ağ Topolojisi & Güvenlik Matrisi (VPC & Network Map)

```mermaid
flowchart TD
    subgraph InternetLayer [Genel İnternet & Dış İstemciler]
        WebUsers[💻 Web Tarayıcıları / Ziyaretçiler]
        TelegramClients[📱 Telegram API Sunucuları]
        APICallers[🔌 REST API & SDK İstemcileri]
    end

    subgraph AWSVPC [AWS Production VPC - 10.0.0.0/16 - us-east-1]
        subgraph PublicSubnets [Public Subnets - Multi-AZ / 10.0.1.0/24 & 10.0.2.0/24]
            ALB["🛡️ AWS Application Load Balancer (ALB)<br/>bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com<br/>• Port 80 (HTTP): Frontend Web<br/>• Port 8000: Backend API & Swagger<br/>• Port 3001: Grafana Canlı İzleme<br/>Security Group: sg-00b8b1417ae80ee0c"]
            NATGateway["🌐 AWS NAT Gateway (Çıkış Yönlü Güvenli İnternet)"]
        end

        subgraph PrivateAppSubnets [Private App Subnets - ECS Fargate Kümesi / 10.0.10.0/24 & 10.0.11.0/24]
            FrontendSvc["🎨 Frontend Service (Port: 3000)<br/>Next.js 14 App Router"]
            BackendSvc["⚙️ Backend Service (Port: 8000)<br/>FastAPI Asenkron Motoru + RAG<br/>Internal DNS: backend.bedrock-gateway.local:8000"]
            TelegramSvc["📱 Telegram Worker Service<br/>Stateful Polling Engine"]
            MonitoringSvc["📊 Monitoring Service (Port: 3000 / 9090)<br/>Grafana 10.4 + Prometheus"]
        end

        subgraph PrivateDataSubnets [Private Isolated Data Subnets / 10.0.20.0/24 & 10.0.21.0/24]
            RDSPostgres["🗄️ AWS RDS PostgreSQL 16 (Multi-AZ)<br/>bedrock-gateway-db.cobqqmqcs7xh.us-east-1.rds.amazonaws.com:5432<br/>Public Access: DISABLED"]
            RedisCluster["⚡ AWS ElastiCache Redis Cluster<br/>bedrock-gateway-redis.hmoplf.0001.use1.cache.amazonaws.com:6379<br/>Public Access: DISABLED"]
        end
    end

    subgraph AWSSaaS [AWS Yönetilen Bulut & Güvenlik Servisleri - SigV4 IAM]
        BedrockService["🧠 AWS Bedrock Foundation Models<br/>• Claude 3.7 Sonnet, Claude 3.5 Haiku<br/>• Amazon Nova Micro, Titan Embeddings"]
        GuardrailsService["🛡️ AWS Bedrock Guardrails<br/>PII Maskeleme & Prompt Injection Koruması"]
        SecretsMgr["🔐 AWS Secrets Manager<br/>bedrock-gateway-secrets-prod"]
        S3Corpus["📦 Amazon S3 Bucket<br/>bedrock-gateway-artifacts-prod"]
        CloudWatchLogs["📝 Amazon CloudWatch Logs<br/>/ecs/bedrock-gateway"]
    end

    InternetLayer -->|Yalnızca Port 80, 8000, 3001| ALB
    ALB -->|Trafik İletimi (Target Group)| FrontendSvc
    ALB -->|Trafik İletimi (Target Group)| BackendSvc
    ALB -->|Trafik İletimi (Target Group)| MonitoringSvc
    TelegramClients <-->|Güvenli Polling| TelegramSvc

    FrontendSvc <-->|İç Ağ VPC İletişimi| BackendSvc
    TelegramSvc <-->|İç Ağ VPC İletişimi| BackendSvc
    MonitoringSvc -->|İç Ağ Metrik Toplama + Bearer Token| BackendSvc

    BackendSvc <-->|Port 5432 (Yalnızca ECS SG İzni)| RDSPostgres
    BackendSvc <-->|Port 6379 (Yalnızca ECS SG İzni)| RedisCluster
    BackendSvc <-->|IAM Task Role / SigV4| S3Corpus
    BackendSvc <-->|IAM Task Role / SigV4| SecretsMgr
    BackendSvc <-->|IAM Task Role / SigV4| GuardrailsService
    GuardrailsService <--> BedrockService

    PrivateAppSubnets -->|Dış Bedrock Çağrıları| NATGateway
    PrivateAppSubnets --> CloudWatchLogs
```

---

## 🔒 2. Güvenlik Grupları (Security Groups) ve İzolasyon Matrisi

Sistemin dışarıdan izinsiz erişim almasını engellemek için **Sıfır Güven (Zero-Trust) Çok Katmanlı Ağ İzolasyonu** uygulanmıştır:

| Katman | Security Group ID | Giriş İzinleri (Inbound Rules) | Çıkış İzinleri (Outbound Rules) | Güvenlik Seviyesi |
| :--- | :--- | :--- | :--- | :--- |
| **ALB (Public)** | `sg-00b8b1417ae80ee0c` | Port 80, 8000, 3001 (`0.0.0.0/0`) | Yalnızca ECS Security Group (`sg-01c2770172f51bca4`) | 🛡️ Filtrelenmiş Public Giriş |
| **ECS Tasks (Private)** | `sg-01c2770172f51bca4` | Port 3000, 8000, 9090 (**Yalnızca ALB SG'den**) | RDS, Redis ve NAT Gateway | 🔒 Tam İzolasyon (Doğrudan Dış Erişim İmkansız) |
| **RDS PostgreSQL (Private)**| `sg-bedrock-rds` | Port 5432 (**Yalnızca ECS SG'den**) | Yok | 🛑 İzole Veri Katmanı (Public IP = DISABLED) |
| **ElastiCache Redis (Private)**| `sg-bedrock-redis` | Port 6379 (**Yalnızca ECS SG'den**) | Yok | 🛑 İzole Önbellek (Public IP = DISABLED) |

---

## 🤖 3. 10 Temel Mimari Bileşenli Otonom Agent Motoru

Platform, otonom yapay zeka ajanlarını 10 modüler bileşen üzerinden yönetir:

### 3.1. Kimlik ve Persona Tanımı (`goal_definition`)
- Her agent için **Rol**, **Hedef Tanımı (`goal_definition`)**, **İletişim Tonu** ve **Sınırları** açıkça yapılandırılır. Model, her göreve bu kimlik çerçevesinde başlar.

### 3.2. 3-Katmanlı Hafıza Motoru (`memory_engine.py` & `semantic_memory.py`)
- **Katman 1 (Kısa Süreli Hafıza):** Son 6 mesaj tam metin tutulur; eski mesajlar tek bir arka plan paragrafına sıkıştırılır (**%75+ token tasarrufu**).
- **Katman 2 (Uzun Süreli Hafıza / Mem0 Standardı):** Kullanıcının tercihleri, uzmanlık alanı, dili ve kuralları yapılandırılmış `SemanticMemoryFact` grafında saklanır. Soruyla ilgili maddeler semantik benzerlikle çekilir.
- **Katman 3 (Çalışma Hafızası / Scratchpad):** Çok adımlı ReAct görevlerinde ara bulgular saklanır.

### 3.3. Native AWS Bedrock Converse API Tool Calling (`bedrock_tools.py`)
- Regex metin taklidi yerine AWS Bedrock'un resmi **`toolConfig`** standardı kullanılır:
  - `web_search`: DuckDuckGo canlı internet ve haber taraması.
  - `python_interpreter`: İzolasyonlu stdout/globals sandbox ortamında güvenli Python kod çalıştırma.
  - `finance_market_data`: Anlık borsa, kripto ve döviz kurları.
  - `schedule_reminder`: Zamanlayıcı ve alarmlar.

### 3.4. ReAct Muhakeme & Öz-Değerlendirme (Self-Reflection)
- Model `Thought ➔ Action ➔ Observation ➔ Reflection (Öz-Değerlendirme)` adımlarını izler. Araçtan gelen veriyi hedefe göre denetler; eksikse ek arama yapar, tamamsa nihai cevabı üretir.

### 3.5. Otonomi Düzeyleri (Human-in-the-Loop)
- **`AUTONOMOUS`:** Görevi baştan sona kendi başına tamamlar.
- **`CONFIRMATION_REQUIRED`:** Kritik eylemlerde kullanıcı onayı ister.
- **`ADVISORY`:** Yalnızca tavsiye ve bilgi sunar.

### 3.6. Maliyetsiz Yerel Vektör RAG (`local_rag.py`)
- Harici pahalı vektör veritabanı gerektirmeden kullanıcı tarafından verilen Website URL'leri veya dokümanlar 450 karakterlik parçalara (overlapping chunks) bölünür; BM25 ve Cosine benzerlik algoritmasıyla sadece en alakalı parçalar prompt'a enjekte edilir.

### 3.7. AWS Bedrock Guardrails & Güvenlik (`guardrails.py`)
- Kredi kartı, telefon ve e-posta numaraları için **PII Maskeleme (Anonymization)**.
- Sistem talimatlarını aşmaya yönelik **Prompt Injection & Jailbreak Koruması**.

### 3.8. Stateful Model Context Protocol (MCP) Server (`mcp_server.py`)
- Standart MCP protokolü ile oturumlar arası bağlam saklama ve dinamik araç çalıştırma yeteneği.

### 3.9. Yaşayan & Büyüyen Ajan (Living Agent IQ - `agent_growth.py`)
- Botlar **🌱 Yenidoğan (Lv 1) ➔ 🌿 Çırak (Lv 2) ➔ 🎓 Uzman (Lv 3) ➔ 👑 Üstat (Lv 4)** seviyelerine yükselir.
- Görev tamamlama (+20 XP), canlı veri işleme (+30 XP) ve kullanıcı beğenileriyle (+50 XP) dinamik IQ puanı artar.

### 3.10. Çok Kanallı İletişim (Web Studio & Telegram Bot)
- Frontier Web Studio ve Telegram Asistan Botu (`@BedrocksAiBot`) aynı hafıza ve model havuzunu paylaşır.
