# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Thai Duong
- **Student ID**: 2A202600650
- **Role**: P5 — Evaluation & Failure Analysis
- **Branch**: Duong
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Dong code | Mo ta |
|---|---|---|
| `src/tools/edu_tools.py` | ~310 | Dataset 15 SV, 14 mon, 8 tool functions + EDU_TOOLS registry |
| `tests/test_cases.py` | ~350 | 34 test cases chia 5 nhom + smoke test runner |
| `tests/run_evaluation.py` | ~170 | Runner so sanh chatbot vs agent, xuat bang + JSON |
| `report/traces/*.md` | 4 files | 1 success trace + 3 failure traces co phan tich |

### Dataset Design

**15 sinh vien** voi do phu phong phu:
- GPA: 1.5 (SV009) → 4.0 (SV014), phu tap tat ca tier hoc bong
- Nam hoc: 1-4, da dang kien thuc nen
- Edge cases: GPA 2.0 dung nguong canh bao (SV013), GPA 4.0 (SV014)

**14 mon hoc** tao thanh do thi tien quyet 4 tang:
```
Tang 0 (khong co tien quyet): CS101, MATH101, ENG101
Tang 1 (can tang 0):          MATH201, DB201, STAT201, ENG201, NET301
Tang 2 (can tang 1):          ML301, SE301, CV301
Tang 3 (can tang 2):          DL401
Tang 4 (can tang 3):          NLP401, CAPSTONE
```
Chuoi tien quyet dai nhat: CS101 → MATH201 → ML301 → DL401 → NLP401 (4 cap).

### Test Case Design (34 cases)

```
Simple  (10): 1 tool call  — kiem tra tung tool doc lap
Multi    (8): 2-3 tools    — chatbot hay sai, agent can chain
Golden   (4): 4-5 tools    — demo chinh thuc
Failure  (7): failure trigger — thu trace loi co chu dich
Edge     (5): bien du lieu — GPA nguong, multi-call, tool 2 lan
```

### Evaluation Runner

`run_evaluation.py` ho tro:
- Chay theo nhom: `--group simple | multi | golden | failure | edge | all`
- Heuristic judge: kiem tra keyword tu golden_answer xuat hien trong output
- Xuat bang so sanh + thong ke theo loai query
- Luu ket qua JSON vao `report/evaluation/eval_TIMESTAMP.json`

---

## II. Debugging Case Study (10 Points)

### Case: Hallucinated Tool — F07

**Query**: "Tim mon hoc phu hop nhat cho SV002 de cai thien GPA..."

**Van de phat hien**: Agent goi `recommend_course(SV002, improve_gpa)` — tool khong ton tai.

**Log evidence** (tu `logs/`):
```json
{
  "event": "TOOL_CALL",
  "data": {
    "tool": "recommend_course",
    "args": "SV002, improve_gpa",
    "obs": "ERROR: Tool 'recommend_course' khong ton tai. Chi dung: [...]"
  }
}
```

**Chan doan**:
- Query dung tu "tim mon phu hop nhat" → LLM ngam dinh phai co tool "recommend".
- System prompt v1 chi liet ke ten tool, khong cam ro "khong duoc dat ten tool moi".
- LLM suy luan theo nhu cau → hallucinate tool name theo pattern thong thuong.

**Diem thu vi**: Agent *tu sua* duoc sau loi — o buoc 3 chon `check_prerequisite` + suy luan tu → Final Answer hop ly. Day la hanh vi self-correction tot.

**Fix — Prompt v2**:
```
TUYET DOI chi goi dung ten tool trong danh sach. 
Neu khong co tool phu hop, giai thich bang suy luan, 
KHONG tu dat ten tool moi.
```

**Do luong tac dong**: Sau khi them dong nay vao prompt, chay lai F07 → buoc 2 khong con ERROR, agent di thang vao `list_available_courses`, so buoc giam tu 4 xuong 3.

**Tong ket 3 loai loi da phan tich**:

| Loai | Test ID | Nguon goc | Fix |
|---|---|---|---|
| Parse Error | F05 | Tham so kieu chu thay vi so | Them chi dan "doi so khi co don vi" vao prompt |
| Hallucination | F07 | LLM tu bịa ten tool | Them cam "khong dat ten tool moi" vao prompt |
| Timeout | F04 | max_steps < buoc can thiet | Tang max_steps hoac them guardrail bao cao trung gian |

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Vai tro cua Thought block

Khac biet lon nhat khong phai la "co tool hay khong" ma la **quy trinh suy luan co cau truc**.

Voi Chatbot: LLM dua ra cau tra loi trong 1 buoc duy nhat — khong co co che kiem tra lai. Ket qua la cau tra loi nghe co ve hop ly nhung thieu du lieu thuc te (vi du bao hoc phi tuy chinh sach truong ma khong co con so cu the).

Voi Agent: Moi buoc Thought → Action → Observation tao ra mot vong lap kiem tra-cap nhat. Agent *biet minh chua biet gi* va goi tool de co du lieu truoc khi ket luan. Day chinh la diem tao ra do chinh xac.

Ket qua thuc te tu bai test:
- 10/10 simple cases: ca hai deu tra loi, nhung chatbot hay sai so lieu (khong co ground truth).
- 8/8 multi cases: agent luon ra dung, chatbot fail 6/8 do khong the chain thong tin.
- 4/4 golden cases: chatbot fail toan bo, agent giai duoc ca 4.

### 2. Reliability — Khi nao Chatbot thang?

Chatbot **tot hon Agent** trong 2 truong hop:
1. **Cau hoi 1 buoc, kien thuc chung**: "Giai thich Machine Learning la gi?" — Agent mat ~5x latency de go tool nhung ket qua tuong duong chatbot.
2. **Latency-sensitive**: Chatbot ~800ms vs Agent ~4,200ms cho golden case. Neu ung dung yeu cau response < 1s, agent co the khong phu hop.

Trich dan tu ban do: voi 10 simple cases, winner la DRAW 7 lan — chatbot khong thua kem gi agent ve do chinh xac khi bai chi 1 buoc.

### 3. Observation — Feedback loop lam thay doi quyet dinh

Observation co gia tri lon nhat khi no **chuan chinh sai lam**:
- Trong F05 (parse error): Observation "could not convert string to float" khien agent tu chuyen doi chu→so o buoc 2. Khong co observation nay, agent se tra loi sai.
- Trong F07 (hallucination): Observation "Tool khong ton tai" khien agent chon strategy khac hoan toan.

Day la co che ma chatbot hoan toan khong co: mot chatbot sau khi dua ra cau tra loi sai khong co cach nao tu biet va tu sua.

---

## IV. Future Improvements (5 Points)

### 1. Mo rong len RAG (Retrieval-Augmented Generation)

Hien tai toan bo du lieu la mock dict trong Python. De len production:
- Chuyen `_STUDENTS` va `_COURSES` vao CSDL (PostgreSQL).
- Them tool `semantic_search_courses(description)` dung vector DB (Qdrant/Weaviate) → tim mon bang mo ta tu nhien thay vi phai biet ma mon chinh xac.
- Viec hoi "Tim mon ve hoc may" se tim duoc ML301, DL401, NLP401 thay vi bao loi.

### 2. Multi-Agent Architecture

Chia thanh 2 agent chuyen biet:
- **Retrieval Agent**: chuyen lay thong tin (get_student_record, check_prerequisite).
- **Reasoning Agent**: nhan du lieu tu Retrieval Agent, tinh toan va dua ra khuyen nghi.

Loi ich: parallelism (2 mon co the kiem tra cung luc), scale don gian, de debug tung agent rieng.

### 3. Guardrails & Safety

- **Input validation**: sanitize student_id (chi cho phep SVxxx format) truoc khi truyen vao tool.
- **Output validator**: kiem tra Final Answer co chua so lieu truoc khi tra ve (neu khong co → yeu cau agent tinh toan lai).
- **Confidence score**: neu agent tra loi "khong co du lieu", log kem confidence de analyst review.

### 4. Cost Optimization

- **Prompt caching**: system prompt it thay doi → cache o provider level (giam ~60% prompt token cost).
- **Tool routing**: voi simple query (1 tu khoa, 1 entity), bypass ReAct loop, goi thang tool → giam latency 5x.
- **Model routing**: dung gpt-4o-mini cho simple, gpt-4o chi cho golden/complex cases.

---

> **Nop bai**: File nay duoc dat tai `report/individual_reports/REPORT_DUONG.md`  
> **Branch**: `Duong`  
> **Commit**: feat(P5)
