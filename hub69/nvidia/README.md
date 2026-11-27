# HUB 69 NVIDIA Adapter

Ứng viên sandbox dùng chung cho 6789, 6788 và 6776. Cài phụ thuộc trong môi trường Python riêng. Các hàm chỉ gọi dịch vụ khi được gọi trực tiếp.

| Tác vụ | Điểm vào | Điều kiện |
| --- | --- | --- |
| Bell pair trên CUDA-Q | `python -m hub69.nvidia.adapter` | Gói `cudaq`, target `qpp-cpu` |
| Bell pair trên GPU | `python -m hub69.nvidia.adapter --target nvidia` | CUDA-Q, GPU tương thích, cuStateVec |
| NIM Chat | `nim_chat(base_url, model, messages)` | NIM endpoint đã cấp phép. Nếu có token, truyền qua `api_key` từ kho bí mật. |
| Kiểm tra ACE | `ace_health(target, service="")` | ACE endpoint có gRPC Health Checking, gói `grpcio-health-checking`. TLS mặc định. |

NIM dùng API Chat Completions và không theo chuyển hướng HTTP. ACE hiện cung cấp kiểm tra trạng thái phục vụ qua gRPC. Chạy một lượt Audio2Face và lưu Evidence riêng trước khi nghiệm thu luồng hoạt ảnh. Các backend GPU và endpoint thật cần kiểm thử tại sandbox đã có quyền và tài nguyên.

Chạy lệnh từ gốc repo. Đầu vào của NIM phải đến từ cấu hình tin cậy. Khi ghép CUDA-Q vào worker có mã khác cũng đổi target, chạy tác vụ trong tiến trình riêng để cô lập cấu hình target.
