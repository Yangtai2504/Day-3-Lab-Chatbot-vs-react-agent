# Trace That Bai — Timeout / Infinite Loop (F04)

**Test ID**: F04  
**Type**: failure_trigger  
**Query**:
> "Cho toi biet SV001 du dieu kien hoc tat ca cac mon thuoc khoa Tri tue nhan tao khong, liet ke tung mon mot."

**Loai loi**: TIMEOUT — agent het buoc (max_steps=5) truoc khi hoan thanh  
**Log event**: `AGENT_END` voi `"status": "max_steps"`  

---

## Full Trace (max_steps = 5)

```
Question: Cho toi biet SV001 du dieu kien hoc tat ca cac mon thuoc khoa
          Tri tue nhan tao khong, liet ke tung mon mot.

--- BUOC 1 ---
Thought: Truoc tien can lay danh sach cac mon thuoc khoa Tri tue nhan tao.
Action: list_available_courses(Tri tue nhan tao)
Observation: Danh sach mon hoc:
  ML301: Machine Learning | 3 tin chi | Tien quyet: CS101, MATH201
  CV301: Thi giac may tinh | 3 tin chi | Tien quyet: CS101, MATH201, ML301
  DL401: Deep Learning | 4 tin chi | Tien quyet: ML301, MATH201
  NLP401: Xu ly ngon ngu tu nhien | 4 tin chi | Tien quyet: ML301, DL401

--- BUOC 2 ---
Thought: Co 4 mon: ML301, CV301, DL401, NLP401.
         Can lay ho so SV001 de biet da hoc nhung mon nao.
Action: get_student_record(SV001)
Observation: SV SV001 — Nguyen Van An | GPA: 3.2 |
             Da hoc: ['CS101', 'MATH101', 'MATH201']

--- BUOC 3 ---
Thought: Kiem tra dieu kien ML301 truoc.
Action: check_eligibility(SV001, ML301)
Observation: SV SV001 (Nguyen Van An) DU dieu kien hoc ML301.

--- BUOC 4 ---
Thought: ML301 du roi. Kiem tra CV301.
Action: check_eligibility(SV001, CV301)
Observation: SV SV001 (Nguyen Van An) CHUA du dieu kien hoc CV301.
             Thieu mon tien quyet: ['ML301']

--- BUOC 5 ---
Thought: CV301 chua du. Con DL401 va NLP401 chua kiem tra.
         Kiem tra DL401.
Action: check_eligibility(SV001, DL401)
Observation: SV SV001 (Nguyen Van An) CHUA du dieu kien hoc DL401.
             Thieu mon tien quyet: ['ML301']

=== HET BUOC (max_steps = 5) ===
LOG: AGENT_END {"steps": 5, "status": "max_steps"}

Agent tra ve: "Da dat gioi han so buoc (timeout)."
```

---

## Phan tich loi

**Van de**:
- Query yeu cau kiem tra **4 mon** nhung moi mon can 1 buoc rieng `check_eligibility`.
- Tong buoc can thiet: 1 (list) + 1 (record) + 4 (check x 4 mon) = **6 buoc**.
- `max_steps = 5` → agent het buoc o buoc 5, **chua kiem tra duoc NLP401**.

**Log tuong ung**:
```json
{"event": "AGENT_START", "data": {"input": "Cho toi biet SV001...", "model": "gpt-4o-mini"}}
{"event": "TOOL_CALL",   "data": {"tool": "list_available_courses", ...}}
{"event": "TOOL_CALL",   "data": {"tool": "get_student_record", ...}}
{"event": "TOOL_CALL",   "data": {"tool": "check_eligibility", "args": "SV001, ML301", ...}}
{"event": "TOOL_CALL",   "data": {"tool": "check_eligibility", "args": "SV001, CV301", ...}}
{"event": "TOOL_CALL",   "data": {"tool": "check_eligibility", "args": "SV001, DL401", ...}}
{"event": "AGENT_END",   "data": {"steps": 5, "status": "max_steps"}}
```

---

## Root Cause

| Nguyen nhan | Mo ta |
|---|---|
| max_steps qua thap | 5 buoc khong du cho query can 6+ buoc |
| Khong co batching | Agent kiem tra tung mon 1 luc thay vi dua ra ket qua trung gian som |
| Thieu guardrail | Agent khong bao cao ket qua mot phan khi sap het buoc |

---

## Fix chon 1 trong 2

**Option A — Tang max_steps** (don gian nhat):
```python
agent = ReActAgent(llm=llm, tools=EDU_TOOLS, max_steps=10)
```

**Option B — Guardrail: bao cao ket qua trung gian** (prompt v2):
```
Neu so buoc con lai <= 1 ma van chua xong toan bo yeu cau,
hay tra Final Answer voi ket qua da co va ghi ro nhung phan chua kiem tra duoc.
Vi du: "Da kiem tra ML301 (du), CV301 (chua du). Con DL401, NLP401 chua kiem tra duoc do het gioi han."
```

**Ket qua sau fix (Option B)**:
```
(Buoc 5) Thought: Con 1 buoc, chua kiem tra het. Bao cao ket qua trung gian.
Final Answer: Ket qua kiem tra SV001 voi cac mon AI:
  - ML301: DU dieu kien
  - CV301: CHUA du (thieu ML301)
  - DL401: CHUA du (thieu ML301)
  - NLP401: Chua kiem tra (het gioi han buoc)
Goi y: SV001 nen hoc ML301 truoc de mo khoa cac mon nang cao.
```
