"""ID Số CFP+: chuỗi chữ số, giữ số 0 đầu, chữ số đầu = Chương, 5 Nhóm.

Cấp bậc theo độ dài: 1 chữ số = Chương, 2 = Con, 3 = Cháu, 4+ = Siêu Bộ Tam 4 • 5 • 6+ số.
Không cấp ID mới: chỉ kiểm tra định dạng của ID được truyền vào.
"""

import re

CHAPTER_GROUP = {"0": "000", "1": "135", "3": "135", "5": "135",
                 "2": "246", "4": "246", "6": "246", "7": "789", "8": "789", "9": "789"}
LEVELS = {1: "CHUONG", 2: "CON", 3: "CHAU"}
_ID = re.compile(r"^[0-9]{1,12}$")


class InvalidID(ValueError):
    pass


def classify(cfp_id: str) -> dict:
    if not isinstance(cfp_id, str) or not _ID.match(cfp_id):
        raise InvalidID(f"ID Số không hợp lệ: {cfp_id!r} (chỉ chữ số 0–9, 1–12 ký tự)")
    n = len(cfp_id)
    return {
        "id": cfp_id,
        "chapter": cfp_id[0],
        "group": CHAPTER_GROUP[cfp_id[0]],
        "level": LEVELS.get(n, f"SIEU_BO_TAM_{n}_SO"),
    }
