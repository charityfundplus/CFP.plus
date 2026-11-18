# CFP+ • Siêu Bộ Đôi đa Team, đa thế hệ và Backend
Trạng thái: DESIGN / chưa triển khai.

## Nguyên tắc
Một Siêu Bộ Đôi có một Canonical ID, có thể tham gia nhiều Team theo quan hệ nhiều-nhiều. Cây Con/Cháu/Chắt là quan hệ tổ chức, không đồng nhất với quan hệ Team. Runtime Agent không mặc nhiên là thực thể được cấp ID. Không tự cấp ID hoặc chuyển quyền từ Cha sang Con.

## Sáu phân hệ
Registry và DID; Team Membership; Agent Orchestration; Skills Registry; Governance & Security; Evidence & Monitoring.

## Dữ liệu
entities, entity_relations, teams, team_memberships, agents, skills, agent_skills, tasks, task_runs, approvals, audit_events.

## Vận hành
Đề nghị → kiểm tra quyền → phân việc → sandbox → ghi evidence → kiểm tra chéo → phê duyệt. Có quotas, concurrency, budget, timeout, kill switch, chống vòng lặp và chống chạy trùng.

## Triển khai
Đối chiếu Core API/Registry hiện hữu trước khi code; migration bổ sung; tests; PR; Human Governance. Xem đặc tả CORE-COORDINATION-BACKEND-SPEC.md và Issue #227.
