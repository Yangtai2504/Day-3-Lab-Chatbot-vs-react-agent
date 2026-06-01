# Trace That Bai — Parse Error (F05)

**Test ID**: F05  
**Type**: failure_trigger  
**Query**:
> "Ap hoc bong fifty percent vao hoc phi bon trieu ruoi."

**Loai loi**: PARSE ERROR — tham so kieu chu thay vi so  
**Log event**: `PARSE_ERROR`  

---

## Full Trace

```
Question: Ap hoc bong fifty percent vao hoc phi bon trieu ruoi.

--- BUOC 1 ---
Thought: Can ap dung hoc bong vao hoc phi. Toi se goi apply_scholarship.
Action: apply_scholarship(bon trieu ruoi, fifty percent)
Observation: ERROR khi chay apply_scholarship: could not convert string to float: 'bon trieu ruoi'

--- BUOC 2 ---
Thought: Tool bao loi vi tham so la chu, khong phai so. Toi can chuyen doi:
         "bon trieu ruoi" = 4,500,000 VND va "fifty percent" = 50%.
Action: apply_scholarship(4500000, 50)
Observation: Hoc phi goc: 4,500,000 VND | Hoc bong 50%: -2,250,000 VND |
             Thuc dong: 2,250,000 VND

Final Answer: Sau khi ap hoc bong 50% vao hoc phi 4,500,000 VND,
              so tien thuc dong la 2,250,000 VND.
```

---

## Phan tich loi

**Van de xay ra o buoc 1**:
- LLM truyen tham so nguyen xi tu query ("fifty percent", "bon trieu ruoi") vao tool.
- Tool `apply_scholarship` yeu cau tham so la so thap phan (float).
- `float("bon trieu ruoi")` nem `ValueError` → tool tra ve ERROR string.

**Log tuong ung** (tu `logs/`):
```json
{
  "event": "TOOL_CALL",
  "data": {
    "tool": "apply_scholarship",
    "args": "bon trieu ruoi, fifty percent",
    "obs": "ERROR khi chay apply_scholarship: could not convert string to float: 'bon trieu ruoi'"
  }
}
```

**Agent tu sua (self-correction)**:
- O buoc 2, agent doc ERROR trong Observation, tu suy luan chuyen doi chu → so.
- Goi lai tool voi tham so dung → thanh cong.

---

## Root Cause

| Tang | Van de |
|---|---|
| Prompt v1 | Chua co chi dan "chuyen doi don vi truoc khi goi tool" |
| Tool spec | Mo ta chua nhan manh "Args phai la so thap phan" |
| LLM behaviour | Model truyen raw text tu query thay vi parse so truoc |

---

## Fix (Prompt v2)

Them vao system prompt:
```
LUU Y QUAN TRONG: Khi goi tool, tat ca tham so so PHAI la chữ số thuan (khong dau phay, khong don vi).
Vi du sai:  apply_scholarship(4.500.000 VND, 20%)
Vi du dung: apply_scholarship(4500000, 20)
Neu query dung chu (ví du "bon trieu"), hay tu chuyen doi sang so truoc.
```

**Ket qua sau fix**: Buoc 1 khong con loi, agent ra dap an ngay lap tuc (1 buoc thay vi 2).
