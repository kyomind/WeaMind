# WeaMind K8s 實作進度

## Day 1 - 基礎設施準備（2026-01-04）

- [x] Hetzner Cloud 開設 3 台 VM（1 控制平面 + 2 工作節點）
- [x] 建立私有網路（Private Network）確保內網互通
- [x] 配置防火牆規則（允許 SSH 從原 VM 堡壘機連入，K8s 節點不暴露公網）
- [x] 設定 SSH 跳板（透過原 VM 訪問 K8s 節點）
- [x] 系統基礎準備（`apt update && upgrade`，安裝必要工具）
- [x] 架構決策：三台節點直接使用 root（網路層已封死，單人操作，符合狠人思維）

---

## Day 2-4 - 控制平面安裝（2026-01-05 至 2026-01-07）

- [x] 控制平面安裝 K3s server（使用 `--disable traefik`，以降低初期變數），並確認 `k3s` 服務為 active (running)
- [x] 取得 node-token（`/var/lib/rancher/k3s/server/node-token`），並保存於堡壘機個人帳號家目錄（僅作為 worker join 使用）
- [x] 複製 kubeconfig（`/etc/rancher/k3s/k3s.yaml`）到本機，並移至標準位置 `~/.kube/config`
- [x] 設定本機 kubectl 透過 SSH tunnel 存取 API server（`-L 6443:127.0.0.1:6443`），kubeconfig 的 server 指向 `https://127.0.0.1:6443`
- [x] 驗證控制平面健康：本機執行 `kubectl get nodes`，顯示 control-plane 節點為 Ready

---

## Day 5-6 - 工作節點加入（2026-01-08 至 2026-01-09）

- [x] 工作節點 1 安裝 K3s agent（使用控制平面內網 IP `10.0.0.3` 與 node-token 加入叢集），確認 `k3s-agent` 服務為 active (running)
- [x] 工作節點 2 安裝 K3s agent（使用相同的 K3S_URL 與 node-token），確認 `k3s-agent` 服務為 active (running)
- [x] 驗證三節點叢集健康：本機執行 `kubectl get nodes`，應顯示 1 個 control-plane + 2 個 worker，且全部為 Ready
- [x] 確認節點間內網通訊正常：於 worker 節點使用內網 IP ping control-plane 與另一台 worker，封包 0% loss
- [x] 檢查節點角色顯示：control-plane 節點顯示 `control-plane`，worker 節點 `ROLES` 為 `<none>`（K3s 預設行為，屬正常狀態）

---

## Day 7-8 - Traefik 與網路驗證（2026-01-10 至 2026-01-11）

- [x] 啟用內建 Traefik Ingress Controller：移除 `--disable traefik` 並重啟 K3s，確認 Ingress controller 正式接管叢集入口流量
- [x] 關鍵修正：強制綁定私有網路介面，明確指定 `--node-ip` 與 `--flannel-iface`，避免 Hetzner 環境誤抓公網 IP 導致 flannel / Service routing 異常
- [x] 驗證 Traefik 系統元件狀態：`traefik` Pod 為 Running，`svclb-traefik` 於各節點建立，確認 entrypoint 已在每個 node 開放
- [x] 驗證叢集內部 Service 通訊：Pod 可透過 Service DNS（如 `http://nginx`）成功存取後端，確認 kube-proxy / CoreDNS / Endpoint 正常
- [x] 部署測試用 nginx（最小 Deployment + Service + Ingress）：完整驗證 Pod 調度、Service 代理、Traefik Ingress Host routing 全鏈路
- [x] 驗證 CoreDNS 解析能力：Pod 內成功解析 `kubernetes.default.svc.cluster.local`，確認 cluster DNS search domain 與 API Service 正常

---

## Day 9 - 應用程式準備（2026-01-12）

- [x] WeaMind repo 新增 `/health` endpoint（FastAPI 簡單返回 `{"status": "ok"}`）
- [x] 複製配置文件到 `weamind-infra/reference/`（Dockerfile、docker-compose.yml、docker-compose.prod.yml、Makefile）
- [x] 從堡壘機 `.env` 生成 `weamind-infra/.env.example`（僅保留 key，清空 value）
- [x] 配置 `.gitignore`：`.env`、`.privatedocs/secrets/`、`kubeconfig.yaml`
- [x] 在堡壘機測試 Docker Compose 單機版服務的 `/health` endpoint（`curl https://api.kyomind.tw/health` 回應 `{"status":"ok"}`）

---

## Day 10-12 - 容器化與 GHCR 自動發布（2026-01-13 至 2026-01-15）

- [x] WeaMind 建立 `publish-ghcr.yml` workflow：CI 成功後自動發布 `latest` 和 `sha-xxx` tags（使用 `workflow_run` 機制`）
- [x] WeaMind 建立 `publish-release.yml` workflow：git tag 觸發，產出語義化版本號（如 `1.0.7`, `1.0`, `1`）
- [x] 兩個 workflows 皆添加多平台支援（`linux/amd64` 和 `linux/arm64`）
- [x] WeaMind 修改 `docker-compose.yml`：從本地 build 改為使用 `ghcr.io/kyomind/weamind:latest`
- [x] 設定 GHCR package 為 public（允許無認證 pull）
- [x] 驗證流程：本地成功 pull image（Apple Silicon）與 Bastion 部署成功

---

## Day 13-14 - 撰寫 line-bot Manifests（2026-01-16 至 2026-01-17）（2-3h）

- [x] 建立 `manifests/namespace.yaml`：定義 `weamind` namespace，作為所有 K8s 資源的隔離邊界
- [x] 撰寫 `manifests/configmap.yaml`：僅放非敏感配置，來源對齊 `.env.example`
- [x] 明確使用堡壘機內網 IP（`10.0.0.2`）作為 `POSTGRES_HOST` 與 `REDIS_URL`，避免誤用 localhost 或 Service 名稱
- [x] 修正 PostgreSQL 對 K8s 實際可連通的 host port（`POSTGRES_PORT=5433`），依據 `nc` 內網連線驗證結果
- [x] 移除 K8s line-bot 不需要的帳號設定（`WEA_DATA_USER`），維持最小權限與最小設定集合
- [x] 驗證 ConfigMap 套用結果，確認 data key 數量與實際內容符合預期（`kubectl get cm -o yaml`）

- [x] 撰寫 `.privatedocs/secrets/secret.yaml`：改用 `stringData` 明文定義敏感資料，避免手動 base64 與 UTF-8 編碼錯誤，**不提交 Git**
- [x] 釐清 Secret 關鍵規則：人手撰寫一律使用 `stringData`，僅在確定為 base64 時才使用 `data`
- [x] 排查並修復 `CreateContainerError (invalid UTF-8)`：根因為錯誤使用 `data` + 非 base64 字串
- [x] 驗證 Secret 套用結果與 Deployment 行為，確認 Pod 能正確注入敏感環境變數

- [x] 撰寫 `manifests/deployment.yaml`：image `ghcr.io/kyomind/weamind:latest`，2 replicas，command 與 docker-compose 一致
- [x] 設定 readiness / liveness probes 指向 `/health`，確認 Pod 進入 Ready 狀態
- [x] 驗證 Deployment / ReplicaSet 行為，確認僅有單一 active RS，Pods `2/2 Running`

- [x] 建立 `manifests/service.yaml`：ClusterIP Service（port 80 -> targetPort 8000），並修正 selector 對齊 Pod label `app=weamind`，確認 Endpoints 產生
- [x] 建立 `manifests/ingress.yaml`：Traefik Ingress（Host `k8s.kyomind.tw`，path `/`），後端指向 `weamind-line-bot:80`，確認 Backends 綁定正確
- [x] 叢集內驗證 Service：用臨時 curl Pod 呼叫 `http://weamind-line-bot/health` 回 `200 {"status":"ok"}`
- [x] NodePort 驗證 Ingress 路由：在 node 上以 `Host: k8s.kyomind.tw` 打 `http://127.0.0.1:30417/health` 回 `200 {"status":"ok"}`
- [x] Dry-run 驗證 manifests：`kubectl apply --dry-run=client -f manifests/` 全數通過

---

## Day 15 - 內部網路連通性驗證（2026-01-18）（1-1.5h）

- [x] 取得堡壘機內網 IP：透過 `ip addr show` 確認內網介面 `enp7s0`，內網 IP 為 `10.0.0.2/32`（Hetzner Private Network，/32 為雲端路由設計，非傳統子網）
- [x] 驗證 K8s 節點 → 堡壘機內網基本連通性：於 worker 節點以 `nc -zv 10.0.0.2 5433`（PostgreSQL）與 `nc -zv 10.0.0.2 6379`（Redis）確認 TCP 連線可達
- [x] 確認 PostgreSQL 實際對外 port 設定：`docker-compose.yml` 使用 `5433:5432`（避免與其他環境的 5432 衝突），並驗證主機 `0.0.0.0:5433` 正在 listen
- [x] 驗證堡壘機 PostgreSQL 容器狀態：透過 `docker compose exec db psql -U wea_bot -d weamind` 成功登入，並可執行 `\dt` 列出資料表
- [x] 以 K8s Pod 視角驗證 PostgreSQL 連線：使用一次性測試 Pod（`postgres:17.5-bookworm`）連線至 `10.0.0.2:5433`，成功執行 `\dt`
- [x] 以 K8s Pod 視角驗證 Redis 連線：使用測試 Pod（`redis:8.2.1-bookworm`）執行 `redis-cli -h 10.0.0.2 -p 6379 ping`，回應 `PONG`
- [x] 驗證實際 line-bot Pod 環境變數：確認 `POSTGRES_HOST=10.0.0.2`、`POSTGRES_PORT=5433`、`REDIS_URL=redis://10.0.0.2:6379/0` 與 ConfigMap 設計一致

---

## Day 16 - LB 配置與公網打通（2026-01-19）（1-1.5h）

- [x] Hetzner Load Balancer 建立與配置：建立 LB 資源，選擇與 K8s 節點相同 location（Nuremberg），並加入 `weamind-network (10.0.0.0/16)`
- [x] 設定 LB 後端目標：加入 `weamind-002`、`weamind-003` 兩台 worker，使用 **Private IP**，port `80`，避免流量打到 control-plane
- [x] 建立 LB Service：HTTP `80 → 80`，Load Balancing Algorithm 使用 Round Robin（低流量、最低複雜度）
- [x] 設定 LB Health Check：HTTP `/health`，Interval 15s，Retries 3，Expected status `200`
- [x] 排查 LB Health Check 先綠後紅問題：確認 Ingress 為 host-based routing，未帶 Host header 時 `/health` 回 `404`
- [x] 以 worker 節點實測驗證差異：`curl http://127.0.0.1/health` → 404，`curl -H 'Host: k8s.kyomind.tw' http://127.0.0.1/health` → 200
- [x] 修正 LB Health Check 行為：於 Service 設定補上 `Domain: k8s.kyomind.tw`，強制 health check 帶 Host header（DNS 尚未存在亦可）
- [x] 驗證修正結果：Targets 狀態由 Unhealthy 穩定轉為 Healthy，LB 顯示 `All services are healthy`
- [x] 發現 weamind Pods 預設被排程至 control-plane（`weamind-001`），確認原因為 node 無 taint（`Taints: <none>`）
- [x] 簡易修正 Pod 排程位置：對 worker 節點加上 label（`nodepool=worker`），並於 Deployment 加入 `nodeSelector`
- [x] 驗證 Pod 重新排程結果：兩個 weamind Pods 成功分別運行於 `weamind-002`、`weamind-003`

- [x] DNS 配置：於域名服務商新增 `k8s.kyomind.tw` A record，指向 Hetzner LB 公網 IP（`91.98.3.241`），作為 K8s 環境的獨立對外端點（避免與單機環境混用）
- [x] TLS 方案決策：確認 **Hetzner Managed Certificate 僅支援 Hetzner DNS**，在 Cloudflare DNS 架構下不可行，改採 **cert-manager + Cloudflare DNS-01** 為最短可行路徑
- [x] 安裝並配置 cert-manager：以官方 bundle 一次性安裝 CRD / controller / webhook / RBAC，理解其為「叢集層級平台元件」，獨立於應用 namespace
- [x] 建立 ClusterIssuer（Let's Encrypt + Cloudflare）：使用 Cloudflare API Token（最小權限）進行 DNS-01 驗證，**避免佔用 80/443 port**，亦不需調整既有 nginx / certbot 容器
- [x] 申請 `k8s.kyomind.tw` TLS 憑證：建立 Certificate 資源，觀察 cert-manager 建立 CertificateRequest / Challenge 流程，等待 DNS TXT propagation（實測約 1–2 分鐘）
- [x] 更新 Ingress 配置：綁定 TLS Secret `k8s-kyomind-tw-tls`，由 Traefik 於 K8s 內部終止 TLS（非 Hetzner LB）
- [x] Hetzner LB 443 設定調整：新增 **TCP 443 → 443 passthrough** service
- [x] 驗證 HTTPS 端到端通訊：
  - `nc -zv k8s.kyomind.tw 443` 驗證 L4 連通
  - `curl https://k8s.kyomind.tw/health` 驗證 TLS + Ingress + Pod
  - 理解 `curl -I` 回 `405` 為 FastAPI 僅允許 GET（非錯誤）
- [x] 建立 LINE webhook 切換 SOP：整理切換步驟、驗證方式與回滾流程，存放於 `docs/LINE-Webhook-切換流程.md`

---

## Day 17 - LINE Webhook 切換（2026-01-27）（30-45min）

- [x] K8s 環境前置檢查：確認 Pods `2/2 Running`（且實際排程於 worker node）、TLS 憑證有效，`curl https://k8s.kyomind.tw/health` 回應 `200 OK`，排除 LB / Ingress / TLS 層問題
- [x] 更新 LINE Developers webhook URL：初次誤設為 `https://k8s.kyomind.tw/webhook` 導致 LINE Verify 回 `404`，後透過 Pod 內 introspection 確認 FastAPI 實際路由為 `/line/webhook`，修正為 `https://k8s.kyomind.tw/line/webhook` 後 Verify 成功
- [x] 端到端功能測試：實際透過 LINE 發送訊息，確認 webhook 請求成功進入 K8s Pod、Bot 正常回覆，並完成 Redis lock、資料庫寫入與天氣資料查詢
- [x] 觀察 Pod 日誌：執行 `kubectl logs -f <pod-name> -n weamind`，確認 `/line/webhook` 回 `200`、無 exception；同時辨識到殘留 `POST /webhook 404` 為錯誤路徑請求，非系統異常

---

## Day 18 - 文件完成（2026-02-19）（1-1.5h）

- [x] 更新 README.md：撰寫專案簡介、架構概覽、Tech Stack、架構特點、部署概述、決策邏輯
- [x] PROGRESS.md 最終更新：補充實際完成時程
