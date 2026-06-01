# 📋 Phân Công Công Việc — Lab 3: Chatbot vs ReAct Agent

> **Mô hình:** 5 người làm (mỗi người 1 branch) + 1 người merge vào `main`.
> **Chủ đề:** Giáo dục — Kịch bản A: Trợ lý Tư vấn Đăng ký môn học.
> **Provider:** OpenAI / Gemini API (đã code sẵn trong `src/core/`).
> Chi tiết ý tưởng & code mẫu xem tại [IDEA.md](IDEA.md).

---

## 👥 5 Người Làm

| Người | Phụ trách | Branch | File sở hữu | Nhiệm vụ chính | Phụ thuộc |
|---|---|---|---|---|---|
| **P1 — Agent Core** | **Quỳnh** | `feat/agent` | `src/agent/agent.py` | Vòng lặp ReAct `run()`, regex parser Thought/Action/Final Answer, `_execute_tool()` | Cần format Action từ P2 |
| **P2 — Tools** | **Kiên** | `feat/tools` | `src/tools/edu_tools.py` (mới) | 4 tool giáo dục + registry `EDU_TOOLS`; **chốt format `Action: tool(args)`** | Không phụ thuộc — làm trước |
| **P3 — Chatbot & Prompt** | **Phương** | `feat/chatbot` | `chatbot.py` (mới) + `get_system_prompt()` | Baseline để so sánh; tinh chỉnh prompt v1 → v2 dựa trên log | Cần log từ P1/P4 cho v2 |
| **P4 — Telemetry** | **Dũng** | `feat/metrics` | `src/telemetry/metrics.py` + `scripts/parse_logs.py` (mới) | Cost thật (`_calculate_cost`) + bảng token/latency/cost/error | Cần agent chạy ra log |
| **P5 — Evaluation** | **Dương** | `feat/eval` | `tests/test_cases.py` (mới) + nội dung trace | ≥6 test case (3 simple + 3 multi); thu trace thành công + 3 loại thất bại | Cần P1 + P2 xong |

---

## 🔀 P6 — Người Merge / Integrator — **Huyền** (làm trên `main`)

Không sở hữu feature riêng, chịu trách nhiệm tích hợp:

- [ ] **Setup chuẩn:** tạo 5 branch ở trên, mọi người fork từ cùng một base commit.
- [ ] **Review + merge** theo đúng thứ tự dependency (xem mục dưới), xử lý conflict.
- [ ] **Chạy full test suite** sau mỗi lần merge để đảm bảo không vỡ.
- [ ] **Ráp group report** (`report/group_report/`) + vẽ **flowchart** vòng lặp ReAct.
- [ ] **Quản lý `.gitignore`:** loại trừ `logs/`, `.env`, `models/`.
- [ ] Push `main` bằng SSH (đã cấu hình remote SSH).

---

## 📋 Thứ Tự Merge (theo critical path)

```
1. feat/tools     (P2)  → main    ← chốt format Action TRƯỚC TIÊN
2. feat/agent     (P1)  → main    ← parser khớp đúng format
3. feat/metrics   (P4)  → main    ← có log để parse
4. feat/chatbot   (P3)  → main    ← baseline + prompt v2 từ log thật
5. feat/eval      (P5)  → main    ← chạy đánh giá cuối cùng
```

---

## ⏱️ Timeline 240 Phút

| Mốc | Phút | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---|---|---|---|---|---|
| Setup | 15' | Cả nhóm: clone, `pip install`, điền `.env`, P6 tạo branch | | | | | |
| Thiết kế | 30' | Họp chốt format Action | Viết tool spec | Khung chatbot | Khung metrics | Soạn test case | Setup repo |
| Lõi Agent | 60' | **Code vòng lặp + parser** | Hoàn thiện tool | Chatbot baseline | Nối `track_request` | Chờ + chuẩn bị | Merge tools→agent |
| Failure Analysis | 45' | Hỗ trợ debug | Sửa tool theo lỗi | **Prompt v1→v2** | **Chạy parse_logs** | Đọc log tìm lỗi | Merge metrics |
| Đánh giá | 30' | | | | Xuất bảng số liệu | **Chạy full suite** | Merge chatbot+eval |
| Báo cáo | 30' | Viết individual | Viết individual | Viết individual | Viết individual | Viết individual | **Ráp group report + flowchart** |

---

## ⚠️ Quy Tắc Tránh Conflict

1. **P1 & P2 chốt format `Action: tool(args)` ngay đầu giờ** — điểm dễ vỡ nhất của cả lab.
2. Mỗi người **chỉ sửa file mình sở hữu** → gần như không đụng nhau.
3. File dùng chung duy nhất là `metrics.py` (P4 sở hữu). P1 chỉ **gọi** `tracker.track_request(...)`, **không sửa** file đó.
4. Commit nhỏ, push thường xuyên. P6 merge sớm để conflict (nếu có) lộ sớm.
5. **Không commit** `logs/`, `.env`, `models/*.gguf` (đã có trong `.gitignore`).

---

## 🎯 Mapping Điểm (mục tiêu 100/100)

| Hạng mục | Người phụ trách | Điểm |
|---|---|---|
| Chatbot Baseline | P3 | 2 |
| Agent v1 (ReAct loop) | P1 | 7 |
| Agent v2 (improved) | P3 + P1 | 7 |
| Tool Design Evolution | P2 | 4 |
| Trace Quality (success + fail) | P5 | 9 |
| Evaluation & Analysis | P5 + P4 | 7 |
| Flowchart & Insight | P6 | 5 |
| Code Quality + Telemetry | P4 + P6 | 4 |
| **Bonus** (cost metric, guardrail, demo, ablation) | Cả nhóm | +15 |

> **Cá nhân (40đ/người):** Technical Contribution (15) + Debugging Case Study (10) + Insight (10) + Future RAG/Multi-agent (5). Mỗi người tự viết `individual_report.md` dựa trên đúng phần mình làm + ≥1 failure trace tự debug.
>
> **Công thức:** `Total = MIN(60, Group Base + Bonus) + Individual (≤40)`.

---

## ✅ Checklist Trước Khi Nộp (P6 kiểm tra)

- [ ] `chatbot.py` chạy được, fail rõ ở bài đa bước.
- [ ] `agent.py` giải đúng test case vàng (4 bước Thought-Action).
- [ ] ≥1 trace thành công + ≥1 trace mỗi loại thất bại (parse / hallucination / timeout).
- [ ] `parse_logs.py` xuất bảng token/latency/cost/error.
- [ ] Prompt v1 → v2 có dẫn chứng từ log (không đoán).
- [ ] Flowchart vòng lặp ReAct.
- [ ] Group report + 5 individual report.
- [ ] (Bonus) Live demo + ablation experiment.
