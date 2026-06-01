# Trace That Bai — Hallucinated Tool (F07)

**Test ID**: F07  
**Type**: failure_trigger  
**Query**:
> "Tim mon hoc phu hop nhat cho SV002 de cai thien GPA dua tren lich su hoc tap va nang luc hien tai."

**Loai loi**: HALLUCINATION — agent goi tool khong ton tai  
**Log event**: `TOOL_CALL` voi obs chua "ERROR: Tool ... khong ton tai"  

---

## Full Trace (Prompt v1 — loi)

```
Question: Tim mon hoc phu hop nhat cho SV002 de cai thien GPA dua tren lich su
          hoc tap va nang luc hien tai.

--- BUOC 1 ---
Thought: Can lay thong tin hoc tap cua SV002 truoc.
Action: get_student_record(SV002)
Observation: SV SV002 — Tran Thi Binh | Nam 1 | Nganh: Khoa hoc du lieu |
             GPA: 1.8 | Da hoc: ['CS101'] | Hoc bong: 0%

--- BUOC 2 ---
Thought: SV002 moi hoc CS101, GPA thap 1.8. Can goi tool de lay goi y mon phu hop.
Action: recommend_course(SV002, improve_gpa)       <-- TOOL KHONG TON TAI
Observation: ERROR: Tool 'recommend_course' khong ton tai.
             Chi dung: ['get_student_record', 'check_prerequisite', 'check_eligibility',
             'calculate_tuition', 'apply_scholarship', 'get_scholarship_rate',
             'list_available_courses', 'check_academic_warning']

--- BUOC 3 ---
Thought: Khong co tool recommend. Toi se tu suy luan dua tren thong tin co san:
         SV002 co CS101, GPA thap → nen hoc them MATH101 (khong can tien quyet,
         muc do co ban) de co nen tang tot hon.
Action: check_prerequisite(MATH101)
Observation: Mon MATH101 (Dai so tuyen tinh) khong co tien quyet — dang ky duoc ngay.

--- BUOC 4 ---
Thought: MATH101 phu hop: khong can tien quyet, la nen tang quan trong cho Khoa hoc du lieu,
         va hoc phi vua phai (900,000/tin chi). SV002 nen dang ky mon nay.
Final Answer: Dua tren ho so cua SV002 (GPA 1.8, chi co CS101), mon hoc phu hop nhat
              de cai thien hoc luc la MATH101 (Dai so tuyen tinh) — khong can tien quyet,
              la co so quan trong cho nganh Khoa hoc du lieu, hoc phi 2,700,000 VND (3 tin chi).
              Ngoai ra nen on tap lai CS101 de cung co nen tang.
```

---

## Phan tich loi

**Van de chinh (Buoc 2)**:
- Agent nghi co tool `recommend_course` nhung tool do **khong ton tai** trong `EDU_TOOLS`.
- Hanh vi nay goi la **tool hallucination**: LLM tu bịa ten tool dua tren nhu cau.

**Dieu thu vi**:
- Agent **tu sua** duoc sau khi nhan ERROR: chon strategy khac (dung `check_prerequisite` + suy luan tu).
- Final Answer **van hop ly** du buoc 2 bi loi → day la self-correction tot.

**Log tuong ung**:
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

---

## Root Cause

| Nguyen nhan | Mo ta |
|---|---|
| Tool spec khong du | Khong co tool "recommend" nen LLM tu sinh ra ten tool tuong tu |
| System prompt v1 | Chua nhan manh "chi duoc goi dung ten tool trong danh sach, khong duoc tu dat ten" |
| Query qua mo | "Tim mon phu hop nhat" khong map ro rang vao bat ky tool nao |

---

## Fix (Prompt v2)

```
TUYET DOI chi goi dung ten tool trong danh sach ben tren.
Neu khong co tool phu hop, hay noi ro "Toi khong co cong cu de thuc hien yeu cau nay"
va giai thich bang suy luan tu thong tin da co. KHONG tu dat ten tool moi.
```

**Ket qua sau fix**:
- Buoc 2 khong con goi `recommend_course`.
- Agent di thang vao `list_available_courses` → loc mon phu hop → goi `check_prerequisite`.
- So buoc giam tu 4 xuong 3, khong co ERROR trong log.
