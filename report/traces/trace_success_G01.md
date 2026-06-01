# Trace Thanh Cong — G01 (Golden Test Case)

**Test ID**: G01  
**Type**: golden (5 buoc)  
**Query**:
> "SV001 du dieu kien hoc ML301 khong? Neu du, tinh hoc phi 3 tin chi sau khi ap hoc bong theo GPA thuc te cua sinh vien do."

**Provider**: OpenAI gpt-4o-mini  
**Ket qua**: THANH CONG  
**So buoc**: 5 Thought-Action  
**Tong latency**: ~4,200 ms  

---

## Full Trace

```
Question: SV001 du dieu kien hoc ML301 khong? Neu du, tinh hoc phi 3 tin chi
          sau khi ap hoc bong theo GPA thuc te cua sinh vien do.

--- BUOC 1 ---
Thought: Truoc tien toi can biet ML301 yeu cau nhung mon tien quyet nao.
Action: check_prerequisite(ML301)
Observation: Mon ML301 (Machine Learning) yeu cau tien quyet: ['CS101', 'MATH201']

--- BUOC 2 ---
Thought: Toi da biet ML301 can CS101 va MATH201. Bay gio can xem SV001 da hoc
         nhung mon nao de doi chieu.
Action: get_student_record(SV001)
Observation: SV SV001 — Nguyen Van An | Nam 2 | Nganh: Cong nghe thong tin |
             GPA: 3.2 | Da hoc: ['CS101', 'MATH101', 'MATH201'] | Hoc bong: 0%

--- BUOC 3 ---
Thought: SV001 da co CS101 va MATH201 — du dieu kien hoc ML301.
         Tiep theo tinh hoc phi 3 tin chi cua ML301.
Action: calculate_tuition(ML301, 3)
Observation: Hoc phi ML301 (Machine Learning) | 3 tin chi x 1,500,000 = 4,500,000 VND

--- BUOC 4 ---
Thought: Hoc phi goc la 4,500,000 VND. Can biet ty le hoc bong theo GPA 3.2 cua SV001.
Action: get_scholarship_rate(SV001)
Observation: SV SV001 (Nguyen Van An) | GPA 3.2 -> Hoc bong loai Gioi: 20%

--- BUOC 5 ---
Thought: SV001 duoc hoc bong 20%. Ap vao hoc phi 4,500,000 VND.
Action: apply_scholarship(4500000, 20)
Observation: Hoc phi goc: 4,500,000 VND | Hoc bong 20%: -900,000 VND |
             Thuc dong: 3,600,000 VND

Final Answer: SV001 (Nguyen Van An) DU dieu kien hoc ML301 (da hoc du CS101 va MATH201).
Hoc phi 3 tin chi la 4,500,000 VND. Voi hoc bong Gioi (GPA 3.2 -> 20%),
sinh vien thuc te chi phai dong 3,600,000 VND.
```

---

## So sanh voi Chatbot

**Chatbot output (cung query):**
> "ML301 la mon Machine Learning. Thuong mon nay can kien thuc co ban ve toan va lap trinh.
> Hoc phi tuy thuoc vao chinh sach truong. Ban nen lien he phong dao tao de biet them chi tiet."

**Nhan xet**:
- Chatbot tra loi chung chung, **khong co du lieu thuc te**.
- Chatbot **khong biet GPA cua SV001** la bao nhieu de tinh hoc bong.
- Chatbot **khong tinh duoc con so chinh xac** 3,600,000 VND.
- Agent: 5 buoc, dung tool, ra so lieu chinh xac 100%.

---

## Metrics (tu log)

| Metric | Chatbot | Agent |
|---|---|---|
| Latency | ~820 ms | ~4,200 ms |
| Tokens (prompt) | 85 | ~1,840 (tich luy qua 5 buoc) |
| Tokens (completion) | 62 | ~380 |
| Correct? | FAIL | PASS |
| Tool calls | 0 | 5 |

**Nhan xet**: Agent cham hon ~5x nhung cho ket qua dung. Chatbot nhanh nhung vo dung voi bai da buoc.
