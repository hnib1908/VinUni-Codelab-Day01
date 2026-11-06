# Ghi chú Lab 01: LLM API Foundation

Tài liệu ôn tập kèm lời giải mã nguồn. Repo không chứa `exercises.md` được nhắc
trong slide nên đây không phải bộ đáp án cho các câu hỏi chưa được cung cấp.

## Các tham số sinh văn bản

- `temperature` điều chỉnh độ ngẫu nhiên khi chọn token. Giá trị thấp thường
  cho câu trả lời ổn định hơn; giá trị cao làm kết quả đa dạng hơn.
- `top_p` giới hạn lựa chọn vào nhóm token có tổng xác suất đạt ngưỡng p.
  Ví dụ p = 0.9 chỉ giữ nhóm lựa chọn có tổng xác suất khoảng 90%.
- `max_tokens` giới hạn token đầu ra. Token không đồng nhất với từ; văn bản
  tiếng Việt có thể tốn nhiều token cho một từ. Giới hạn quá thấp có thể khiến
  câu trả lời bị cắt; với model có suy luận, ngân sách đầu ra có thể còn bao gồm
  token suy luận.

## Kết quả và chi phí

Mỗi hàm gọi API trả về `(response_text, latency_seconds, usage)`.
`usage` gồm `input_tokens` và `output_tokens`, lấy từ metadata của nhà cung cấp.
Độ trễ được đo bằng `time.perf_counter()` quanh lời gọi API, không gồm bước
khởi tạo client. Không suy ra số token từ độ dài chuỗi.

```text
cost_usd = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
```

Ví dụ theo bảng giá của đề: GPT-4o với 10 token đầu vào và 20 token đầu ra có
chi phí `(10 * 5 + 20 * 20) / 1_000_000 = 0.00045 USD`.
Đây là phép tính minh họa, không phải kết quả gọi API thật.

Khi so sánh, dùng cùng prompt và cùng cấu hình sinh văn bản, rồi đánh giá
độ đúng, tính phù hợp, độ trễ và chi phí. Model rẻ nhất không tự động là model
trả lời tốt nhất. Độ trễ cần được đo nhiều lần để giảm ảnh hưởng của mạng.

## Streaming, lịch sử và retry

Streaming hiển thị từng phần của câu trả lời ngay khi nhận được, giúp người dùng
đọc sớm. Streaming không đảm bảo tổng thời gian sinh câu trả lời ngắn hơn.

Gemini dùng role `user` và `model`. Sau mỗi lượt thành công, lưu cặp câu hỏi và
câu trả lời, rồi cắt còn 6 tin nhắn (3 lượt). Lời gọi kế tiếp gửi tối đa 6 tin
nhắn lịch sử cộng câu hỏi hiện tại. Giới hạn lịch sử giảm lượng token đầu vào
nhưng có thể làm mất ngữ cảnh cũ.

Exponential backoff tăng thời gian chờ sau mỗi lần lỗi. Hàm bonus thử lại mọi
`Exception` theo yêu cầu bài tập và ném lại lỗi cuối khi hết lượt. Trong ứng
dụng thực tế nên chỉ thử lại lỗi tạm thời; lỗi API key không hợp lệ cần sửa cấu
hình. Hàm retry không tự động bọc các lời gọi API của bài lab.

## Tài liệu SDK đã đối chiếu

- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/python/messages/create)
- OpenAI: đối chiếu chữ ký `chat.completions.create` từ SDK cài trên máy.
