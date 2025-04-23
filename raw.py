import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import google.generativeai as genai
import time
import os # Import os library to handle environment variables
import docx
from bs4 import NavigableString


def read_word_file(file_path):
    """
    Đọc toàn bộ nội dung của file Word (.docx) và trả về một chuỗi (string).
    Mỗi đoạn văn (paragraph) được nối cách nhau bằng dòng mới.
    """
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        # Lọc bỏ những đoạn trống hoặc chỉ chứa whitespace
        if para.text.strip():
            full_text.append(para.text.strip())
    return "\n".join(full_text)

reference_content = read_word_file("chuong_trinh_2018.docx")


# --- Configuration ---
# **BEST PRACTICE:** Store your API Key securely, e.g., as an environment variable.
# Replace "YOUR_API_KEY" with your actual key ONLY IF you cannot use environment variables.
# Example for environment variable:
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     raise ValueError("GEMINI_API_KEY environment variable not set.")
# genai.configure(api_key=api_key)

# --- OR (Less Secure - Use with caution) ---
# Dán API Key của bạn vào đây (Paste your API key here)
# Make sure this key is kept private and not shared publicly (e.g., on GitHub)


try:
    genai.configure(api_key="AIzaSyDLO3zdy9ZDL8Rcq9OvMOYxCawDFQG0kUw")
except ValueError as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please ensure you have set the API key correctly.")
    exit() 



# --- Gemini Function ---
# 3. Chỉnh sửa hàm get_additional_info_with_gemini để nhận thêm biến reference_content
def get_additional_info_with_gemini(question_text, correct_ans_letter, ans_a, ans_b, ans_c, ans_d, reference_content):
    # Xác định nội dung đáp án đúng
    correct_ans_text = ""
    if correct_ans_letter == 'A':
        correct_ans_text = ans_a
    elif correct_ans_letter == 'B':
        correct_ans_text = ans_b
    elif correct_ans_letter == 'C':
        correct_ans_text = ans_c
    elif correct_ans_letter == 'D':
        correct_ans_text = ans_d
    else:
        correct_ans_text = f"Không xác định được nội dung đáp án {correct_ans_letter}"

    # Tạo prompt, trong đó có chèn nội dung file Word
    prompt = f"""
Dưới đây là nội dung tham khảo (Chương trình giáo dục phổ thông Tin học 2018):
{reference_content}

Cho câu hỏi trắc nghiệm Tin học sau:
Câu hỏi: {question_text}
A. {ans_a}
B. {ans_b}
C. {ans_c}
D. {ans_d}
Đáp án đúng là: {correct_ans_letter}. {correct_ans_text}

Hãy:
1. Dựa vào cả nội dung tham khảo ở trên và Chương trình giáo dục phổ thông môn Tin học (Ban hành kèm theo Thông tư số 32/2018/TT-BGDĐT) giải thích ngắn gọn, rõ ràng tại sao đáp án '{correct_ans_letter}' là đáp án đúng. Tập trung vào kiến thức cốt lõi liên quan.
2. Dựa vào nội dung tham khảo ở trên xác định câu hỏi {question_text} thuộc chủ đề nào trong số 7 chủ đề sau:
   A. Máy tính và xã hội tri thức
   B. Mạng máy tính và Internet
   C. Tổ chức lưu trữ, tìm kiếm và trao đổi thông tin
   D. Đạo đức, pháp luật và văn hoá trong môi trường số
   E. Ứng dụng tin học
   F. Giải quyết vấn đề với sự trợ giúp của máy tính
   G. Hướng nghiệp với tin học
   Chỉ cần ghi chữ cái và tên chủ đề (ví dụ: E. Ứng dụng tin học).
3. Xác định mức độ nhận thức của câu hỏi theo mô tả từng mức độ trong nội dung tham khảo ở trên (chọn MỘT trong các mức: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao).
4. Câu hỏi {question_text} đáp ứng "Năng lực" nào trong nội dung tham khảo ở trên. Xác định **mã** và **tên** năng lực theo chương trình (ví dụ “NLa. Năng lực sử dụng và quản lý…”).
5. Câu hỏi {question_text} đáp ứng "Yêu cầu cần đạt" nào trong nội dung tham khảo ở trên.

Trả lời theo đúng định dạng sau, không thêm bất kỳ nội dung nào khác:
Giải thích: [Nội dung giải thích]
Chủ đề: [Chữ cái. Tên chủ đề]
Mức độ: [Mức độ nhận thức]
Năng lực: [Mã. Tên năng lực]
Yêu cầu cần đạt: [Nội dung yêu cầu cần đạt]
    """

    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # Hoặc gemini-pro
        response = model.generate_content(prompt)
        text = response.text

        explanation_match = re.search(r"Giải thích:\s*(.*?)(?=\s*(Chủ đề:|Mức độ:|Yêu cầu cần đạt:)|$)", text, flags=re.DOTALL)
        topic_match = re.search(r"Chủ đề:\s*([A-G]\.\s*.*)", text)
        level_match = re.search(r"Mức độ:\s*(Nhận biết|Thông hiểu|Vận dụng|Vận dụng cao)", text)
        competency_match = re.search(r"Năng lực:\s*([A-Za-z0-9]+)\.\s*(.*?)(?=\s*Yêu cầu cần đạt:)",text, flags=re.DOTALL)
        outcome_match = re.search(r"Yêu cầu cần đạt:\s*(.*)", text, re.DOTALL)

        explanation = explanation_match.group(1).strip() if explanation_match else "Không thể phân tích giải thích."
        topic = topic_match.group(1).strip() if topic_match else "Không thể phân tích chủ đề."
        level = level_match.group(1).strip() if level_match else "Không thể phân tích mức độ."
        competency = (f"{competency_match.group(1).strip()}. {competency_match.group(2).strip()}" if competency_match else "Không phân tích được")
        outcome = outcome_match.group(1).strip() if outcome_match else "Không thể phân tích yêu cầu cần đạt."

        return explanation, topic, level, competency, outcome

    except Exception as e:
        print(f"Lỗi khi gọi Gemini hoặc xử lý phản hồi: {e}")
        print(f"Câu hỏi: {question_text}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Prompt Feedback: {response.prompt_feedback}")
        return "Lỗi API", "Lỗi API", "Lỗi API", "Lỗi API"

"""# --- Web Scraping ---
url = "https://tech12h.com/bai-hoc/trac-nghiem-tin-hoc-10-ket-noi-tri-thuc-bai-bien-va-lenh-gan.html"
print(f"Đang tải dữ liệu từ: {url}")

try:
    response = requests.get(url, timeout=30) # Add timeout
    response.raise_for_status() # Check for HTTP errors (like 404, 500)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main content area
    content = soup.find('div', class_='block-content-body')
    if not content:
        print("Lỗi: Không tìm thấy thẻ div có class 'block-content-body'. Cấu trúc trang web có thể đã thay đổi.")
        exit()

    # Find all paragraphs that seem to be questions (more robust)
    # Assumes questions start with "Câu [number]:"
    all_paragraphs = content.find_all('p')
    question_paragraphs = []

    for p in all_paragraphs:
        text = p.get_text(strip=True)  # Lấy text đầy đủ, kể cả thẻ con
        if re.match(r"^\s*Câu\s*\d+\s*:", text, re.IGNORECASE):
            question_paragraphs.append(p)

    print(f"Đã tìm thấy {len(question_paragraphs)} thẻ <p> khớp định dạng câu hỏi.")

    questions_data = []
    question_count = 0
    api_call_delay = 3

    # Iterate through potential question paragraphs
    for p in question_paragraphs:
        question_text_raw = p.get_text().strip()
        # Clean the question text (remove "Câu X:")
                # --- Thu thập toàn bộ text của câu, không chỉ 1 dòng ---
        lines = []
        # 1) Thêm dòng đầu đã strip "Câu X:"
        first = re.sub(r"^\s*Câu\s*\d+\s*:\s*", "", question_text_raw).strip()
        lines.append(first)

        # 2) Duyệt qua các sibling liền kề cho đến khi gặp <ul>
        for sib in p.next_siblings:
            if hasattr(sib, 'name') and sib.name == 'ul':
                break
            # Chỉ quan tâm đến các <p> hoặc text nodes
            if isinstance(sib, NavigableString):
                txt = sib.strip()
                if txt:
                    lines.append(txt)
            elif sib.name == 'p':
                txt = sib.get_text(strip=True)
                if txt:
                    lines.append(txt)

        # 3) Ghép lại thành 1 chuỗi dài
        question_text = " ".join(lines)

        # Find the corresponding answer list (ul) immediately following the question paragraph
        ul = p.find_next_sibling('ul')

        if not ul:
            print(f"Cảnh báo: Không tìm thấy danh sách đáp án (<ul>) ngay sau câu hỏi: '{question_text_raw}'")
            continue # Skip this question if no answer list is found

        answers = ul.find_all('li')
        if len(answers) < 4:
            print(f"Cảnh báo: Tìm thấy ít hơn 4 đáp án cho câu hỏi: '{question_text_raw}'")
            # Pad with empty strings if necessary, or skip
            # continue

        # Extract answer options safely
        ans_a = answers[0].get_text(strip=True).replace('A.', '', 1).strip() if len(answers) > 0 else ''
        ans_b = answers[1].get_text(strip=True).replace('B.', '', 1).strip() if len(answers) > 1 else ''
        ans_c = answers[2].get_text(strip=True).replace('C.', '', 1).strip() if len(answers) > 2 else ''
        ans_d = answers[3].get_text(strip=True).replace('D.', '', 1).strip() if len(answers) > 3 else ''

        # Find the correct answer
        correct_answer_letter = ''
        for idx, li in enumerate(answers):
            # Check if the 'li' contains an 'h6' tag which indicates the correct answer on this site
            if li.find('h6'):
                correct_answer_letter = ['A', 'B', 'C', 'D'][idx]
                break # Found the correct answer, no need to check further



        if not correct_answer_letter:
            print(f"Cảnh báo: Không tìm thấy đáp án đúng (thẻ <h6>) cho câu hỏi: '{question_text_raw}'")
            # Decide how to handle: skip, mark as unknown, etc.
            # For now, we'll try calling Gemini but indicate the answer is unknown
            correct_answer_letter = "?" # Indicate unknown correct answer


        # Get additional info from Gemini API
        question_count += 1
        print(f"\nĐang xử lý câu {question_count}: {question_text[:50]}...") # Print progress
        print(f"   Đáp án đúng dự kiến: {correct_answer_letter}")

        if correct_answer_letter == "?":
             explanation, topic, level, outcome = ("Không thể xác định đáp án đúng từ web",) * 4
        else:
             explanation, topic, level, outcome = get_additional_info_with_gemini(
                 question_text, correct_answer_letter, ans_a, ans_b, ans_c, ans_d, reference_content
             )

        print(f"   => Chủ đề: {topic}, Mức độ: {level}")

        questions_data.append({
            'Câu hỏi': question_text,
            'Đáp án A': ans_a,
            'Đáp án B': ans_b,
            'Đáp án C': ans_c,
            'Đáp án D': ans_d,
            'Đáp án đúng': correct_answer_letter,
            'Giải thích': explanation,
            'Chủ đề': topic,
            'Mức độ': level,
            'Yêu cầu cần đạt': outcome
        })

        # Pause to avoid hitting API rate limits
        print(f"   (Tạm dừng {api_call_delay} giây)")
        time.sleep(api_call_delay)

except requests.exceptions.RequestException as e:
    print(f"Lỗi mạng hoặc HTTP khi truy cập URL: {e}")
    exit()
except Exception as e:
    print(f"Đã xảy ra lỗi không mong muốn trong quá trình scraping: {e}")
    # Optionally print traceback for debugging
    import traceback
    traceback.print_exc()
    exit()

# --- Export to Excel ---
if questions_data:
    try:
        df = pd.DataFrame(questions_data)
        df['Chủ đề'] = df['Chủ đề'].apply(lambda x: x if x.startswith('Chủ đề') else f"Chủ đề {x}")
        output_filename = "cau_hoi_trac_nghiem_mo_rong.xlsx"
        df.to_excel(output_filename, index=False, engine='openpyxl') # Specify engine if needed
        print(f"\n✅ Đã tạo file '{output_filename}' với {len(questions_data)} câu hỏi thành công!")
    except Exception as e:
        print(f"Lỗi khi xuất file Excel: {e}")
else:
    print("\nKhông có dữ liệu câu hỏi nào được thu thập để xuất ra Excel.")"""

# --- Load lại file Excel đã có sẵn (câu hỏi, A–D, đáp án đúng) ---
input_file  = "cau_hoi_trac_nghiem_mo_rong.xlsx"
output_file = "cau_hoi_trac_nghiem_mo_rong_filled.xlsx"
df = pd.read_excel(input_file, engine='openpyxl')
if 'Năng lực' not in df.columns:
    df['Năng lực'] = ""
# --- Cho AI điền 4 cột mới ---
api_delay = 3
for idx, row in df.iterrows():
    # nếu đã có giai_thich rồi thì bỏ qua
    if (pd.notna(row.get('Giải thích')) and pd.notna(row.get('Chủ đề')) and pd.notna(row.get('Năng lực'))):
        continue

    q   = row['Câu hỏi']
    a,b,c,d = row['Đáp án A'], row['Đáp án B'], row['Đáp án C'], row['Đáp án D']
    ans = str(row['Đáp án đúng']).strip()

    print(f"[{idx+1}/{len(df)}] Xử lý: {q[:30]}... Đáp án: {ans}")
    try:
        expl, topic, level, competency, outcome = get_additional_info_with_gemini(
            q, ans, a, b, c, d, reference_content
        )
    except Exception as e:
        print("  -> Lỗi API:", e)
        expl = topic = level = outcome = "Lỗi API"

    df.at[idx, 'Giải thích']      = expl
    # thêm tiền tố "Chủ đề " nếu chưa có
    df.at[idx, 'Chủ đề']          = topic if topic.startswith("Chủ đề") else f"Chủ đề {topic}"
    df.at[idx, 'Mức độ']          = level
    df.at[idx, 'Năng lực']        = competency
    df.at[idx, 'Yêu cầu cần đạt'] = outcome

    time.sleep(api_delay)

# --- Xuất file mới ---
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"✅ Đã điền xong và lưu file: {output_file}")
