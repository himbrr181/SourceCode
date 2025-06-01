import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime, timedelta # Đã thêm timedelta
import requests
import uuid # Thêm thư viện để tạo ID duy nhất
import re # Để kiểm tra định dạng ngày và tìm kiếm
notified_tasks = set()  # Lưu ID task đã thông báo nhắc nhở


# --- Cấu hình và Hằng số ---
DATA_FILE = 'tasks.json'
API_URL = "https://jsonplaceholder.typicode.com/todos" # API mẫu để lấy dữ liệu



# --- Hàm quản lý File JSON ---
def init_data_file():
    """Khởi tạo file JSON nếu chưa tồn tại hoặc rỗng."""
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)

def load_tasks():
    """Đọc dữ liệu từ file JSON."""
    init_data_file() # Đảm bảo file tồn tại trước khi đọc
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        messagebox.showerror("Lỗi dữ liệu", "File JSON bị hỏng. Đang tạo lại file mới.")
        init_data_file() # Tạo lại file nếu JSON bị lỗi
        return []

def save_tasks(tasks):
    """Lưu dữ liệu vào file JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# --- Hàm kiểm tra và xử lý dữ liệu ---
def is_valid_date(date_str):
    """Kiểm tra định dạng ngày dd/mm/yyyy và phải lớn hơn hoặc bằng ngày hiện tại."""
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        return False
    try:
        input_date = datetime.strptime(date_str, '%d/%m/%Y').date()
        today = datetime.now().date()
        return input_date >= today
    except ValueError:
        return False

# Hàm sắp xếp Treeview theo cột (click header)
def treeview_sort_column(tv, col, reverse):
    """Sắp xếp dữ liệu trong Treeview khi click vào header cột."""
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    
    # Định nghĩa thứ tự cho độ ưu tiên và trạng thái
    priority_order = {"Cao": 0, "Thấp": 1}
    status_order = {"Cần thực hiện": 0, "Đang thực hiện": 1, "Đã hoàn thành": 2}

    if col == 'due_date':
        # Sắp xếp theo ngày, nếu ngày không hợp lệ sẽ đẩy xuống cuối
        l.sort(key=lambda t: datetime.strptime(t[0], '%d/%m/%Y') if is_valid_date(t[0]) else datetime.max, reverse=reverse)
    elif col == 'priority':
        l.sort(key=lambda t: priority_order.get(t[0], 99), reverse=reverse) # 99 là giá trị mặc định nếu không khớp
    elif col == 'status':
        l.sort(key=lambda t: status_order.get(t[0], 99), reverse=reverse)
    else: # Các cột text khác (title, description)
        l.sort(key=lambda t: t[0].lower(), reverse=reverse)

    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)
    tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse)) # Đảo ngược thứ tự cho lần click tiếp theo

# --- Chức năng CRUD ---
def add_task():
    """Thêm công việc mới."""
    title = entry_title.get().strip()
    description = entry_description.get("1.0", tk.END).strip()
    due_date = entry_due_date.get().strip()
    priority = priority_var.get()
    status = status_var.get() # Lấy trạng thái

    if not title or not description or not due_date:
        messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
        return
    
    if not is_valid_date(due_date):
        messagebox.showwarning("Cảnh báo", "Ngày hết hạn không hợp lệ! Vui lòng nhập đúng định dạng dd/mm/yyyy và lớn hơn hoặc bằng ngày hiện tại.")
        return

    new_task = {
        "id": str(uuid.uuid4()), # Tạo ID duy nhất cho mỗi công việc
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "status": status # Thêm trạng thái
    }

    tasks = load_tasks()
    tasks.append(new_task)
    save_tasks(tasks)
    messagebox.showinfo("Thông báo", "Công việc đã được thêm thành công!")
    clear_entries()
    refresh_task_list()

def delete_task():
    """Xóa công việc đã chọn."""
    selected_item = treeview_tasks.selection()
    if not selected_item:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn công việc để xóa!")
        return

    # Lấy ID của công việc từ tags của Treeview item (đã lưu khi chèn)
    task_id_to_delete = treeview_tasks.item(selected_item[0], 'tags')[0] 
    title_to_delete = treeview_tasks.item(selected_item[0], 'values')[0]

    if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa công việc: '{title_to_delete}' không?"):
        tasks = load_tasks()
        # Lọc danh sách để tạo danh sách mới không chứa công việc có ID cần xóa
        tasks = [task for task in tasks if task.get("id") != task_id_to_delete]
        save_tasks(tasks)
        messagebox.showinfo("Thông báo", "Công việc đã được xóa thành công!")
        clear_entries()
        refresh_task_list()

def delete_all_tasks():
    """Xóa tất cả các công việc."""
    if messagebox.askyesno("Xác nhận xóa tất cả", "Bạn có chắc chắn muốn xóa TẤT CẢ các công việc không? Thao tác này không thể hoàn tác."):
        save_tasks([]) # Lưu danh sách rỗng
        messagebox.showinfo("Thông báo", "Tất cả công việc đã được xóa!")
        clear_entries()
        refresh_task_list()

def edit_task():
    """Chỉnh sửa công việc đã chọn."""
    selected_item = treeview_tasks.selection()
    if not selected_item:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn công việc để chỉnh sửa!")
        return

    task_id_to_edit = treeview_tasks.item(selected_item[0], 'tags')[0] # Lấy ID từ tags

    title = entry_title.get().strip()
    description = entry_description.get("1.0", tk.END).strip()
    due_date = entry_due_date.get().strip()
    priority = priority_var.get()
    status = status_var.get() # Lấy trạng thái

    if not title or not description or not due_date:
        messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
        return
    
    if not is_valid_date(due_date):
        messagebox.showwarning("Cảnh báo", "Ngày hết hạn không hợp lệ! Vui lòng nhập đúng định dạng dd/mm/yyyy và lớn hơn hoặc bằng ngày hiện tại.")
        return

    tasks = load_tasks()
    
    # Duyệt qua danh sách và cập nhật công việc dựa trên ID
    for i, task in enumerate(tasks):
        if task.get("id") == task_id_to_edit:
            tasks[i] = {
                "id": task_id_to_edit, # Giữ nguyên ID
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
                "status": status
            }
            save_tasks(tasks)
            messagebox.showinfo("Thông báo", "Công việc đã được chỉnh sửa thành công!")
            clear_entries()
            refresh_task_list()
            return # Thoát khỏi hàm sau khi tìm và cập nhật
    messagebox.showerror("Lỗi", "Không tìm thấy công việc để chỉnh sửa.")

# --- Hiển thị và Làm mới ---
def show_task_details(event):
    """Hiển thị chi tiết công việc được chọn lên các trường nhập liệu."""
    selected_item = treeview_tasks.selection()
    if not selected_item:
        # Nếu không có gì được chọn (ví dụ: click ra ngoài)
        clear_entries()
        return

    # Lấy các giá trị từ hàng được chọn trong Treeview
    # values = (title, due_date, priority, status, description)
    item_values = treeview_tasks.item(selected_item[0], 'values')
    
    if len(item_values) >= 5: # Đảm bảo có đủ các giá trị
        entry_title.delete(0, tk.END)
        entry_title.insert(0, item_values[0]) # Tiêu đề
        
        entry_description.delete("1.0", tk.END)
        entry_description.insert("1.0", item_values[4]) # Mô tả (cột ẩn)
        
        entry_due_date.delete(0, tk.END)
        entry_due_date.insert(0, item_values[1]) # Ngày hết hạn
        
        priority_var.set(item_values[2]) # Độ ưu tiên
        status_var.set(item_values[3]) # Trạng thái
    else:
        messagebox.showwarning("Lỗi", "Không đủ dữ liệu cho mục đã chọn.")
        clear_entries()
def parse_due_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except (ValueError, TypeError):
        return datetime.strptime("01/01/2100", '%d/%m/%Y')
def refresh_task_list():
    """Làm mới danh sách công việc trên Treeview dựa trên bộ lọc và tìm kiếm."""
    for item in treeview_tasks.get_children():
        treeview_tasks.delete(item)

    tasks = load_tasks()
    
    # Áp dụng tìm kiếm
    search_term = search_entry.get().strip().lower()
    if search_term:
        tasks = [task for task in tasks if 
                 search_term in task.get("title", "").lower() or 
                 search_term in task.get("description", "").lower()]
    
    # Áp dụng bộ lọc ưu tiên
    filter_priority = filter_priority_var.get()
    if filter_priority != "Tất cả":
        tasks = [task for task in tasks if task.get("priority") == filter_priority]

    # Áp dụng bộ lọc trạng thái
    filter_status = filter_status_var.get()
    if filter_status != "Tất cả":
        tasks = [task for task in tasks if task.get("status") == filter_status]
  # Ngày mặc định rất xa để xếp cuối

    # Sắp xếp lại danh sách sau khi lọc và tìm kiếm
    sorted_tasks = sorted(tasks, key=lambda x: (
    0 if x.get("priority") == "Cao" else 1,
    parse_due_date_safe(x.get("due_date", "01/01/2100"))
))
    
    # Chèn dữ liệu vào Treeview
    for task in sorted_tasks:
        # Gán tags cho từng hàng để dễ dàng lấy ID khi xóa/sửa
        # Đảm bảo các trường tồn tại trước khi truy cập
        task_id = task.get("id", "")
        title = task.get("title", "")
        due_date = task.get("due_date", "")
        priority = task.get("priority", "")
        status = task.get("status", "")
        description = task.get("description", "") # Cột mô tả sẽ được ẩn

        # Xác định màu sắc dựa trên ưu tiên và trạng thái
        tags = (task_id,) # Tag đầu tiên là ID của công việc
        if status == "Hoàn thành":
            tags += ("done_task",) # Màu xanh lá
        elif priority == "Cao":
            tags += ("high_priority",) # Màu đỏ
        elif priority == "Thấp":
            tags += ("low_priority",) # Màu xanh dương nhạt

        treeview_tasks.insert("", tk.END, values=(title, due_date, priority, status, description), tags=tags)
        
        # Nhắc nhở công việc sắp đến hạn (Hiển thị popup)
        check_due_date_reminder(task)

def clear_entries():
    """Xóa nội dung của các trường nhập liệu."""
    entry_title.delete(0, tk.END)
    entry_description.delete("1.0", tk.END)
    entry_due_date.delete(0, tk.END)
    priority_var.set("Cao")
    status_var.set("Cần thực hiện")

def check_due_date_reminder(task):
    """Kiểm tra và hiển thị nhắc nhở nếu công việc sắp đến hạn, chỉ hiện 1 lần mỗi task."""
    global notified_tasks

    task_id = task.get("id")
    if not task_id:
        return

    if task.get("status") == "Hoàn thành":  # Không nhắc công việc đã hoàn thành
        return

    # Nếu task đã được thông báo rồi thì không hiện nữa
    if task_id in notified_tasks:
        return

    try:
        due_date_dt = datetime.strptime(task.get("due_date"), '%d/%m/%Y').date()
        today = datetime.now().date()
        days_left = (due_date_dt - today).days

        if 0 <= days_left <= 3:
            messagebox.showinfo("Nhắc nhở công việc",
                                f"Công việc '{task.get('title')}' sắp đến hạn!\n"
                                f"Ngày hết hạn: {task.get('due_date')}\n"
                                f"Còn {days_left} ngày.")
            notified_tasks.add(task_id)  # Đánh dấu đã thông báo
    except (ValueError, TypeError):
        pass


# --- Chức năng Tải dữ liệu từ API ---
def fetch_and_add_from_api():
    """Tải dữ liệu công việc từ API mẫu và chỉ thêm các công việc có ID cụ thể với nội dung tùy chỉnh."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status() # Kiểm tra lỗi HTTP (ví dụ: 404, 500)
        api_data = response.json()

        tasks_to_add = []
        for item in api_data:
            original_id = item.get("id", "N/A")

            # --- BẮT ĐẦU PHẦN TÙY CHỈNH NỘI DUNG VÀ LỌC ---

            custom_title = ""
            custom_description = ""
            custom_due_date = ""
            custom_priority = ""
            custom_status = ""

            if original_id == 1:
                custom_title = "Đi học"
                custom_description = "Chuẩn bị sách vở, đồng phục và đến trường đúng giờ. Đừng quên bài tập về nhà!"
                custom_due_date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y') 
                custom_priority = "Cao"
                custom_status = "Cần thực hiện"
            elif original_id == 2:
                custom_title = "Đi làm thêm ca tối"
                custom_description = "Hoàn thành các nhiệm vụ được giao tại nơi làm thêm. Giao tiếp tốt với đồng nghiệp và về nhà an toàn."
                custom_due_date = (datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y') 
                custom_priority = "Cao"
                custom_status = "Đang thực hiện"
            elif original_id == 3:
                custom_title = "đi chơi "
                custom_description = "giải trính."
                custom_due_date = (datetime.now() + timedelta(days=6)).strftime('%d/%m/%Y') 
                custom_priority = "Thấp"
                custom_status = "Hoàn thành"
            else:
                # Nếu không khớp với bất kỳ ID cụ thể nào, BỎ QUA công việc này
                continue # Dòng này sẽ bỏ qua các công việc không khớp điều kiện

            # --- KẾT THÚC PHẦN TÙY CHỈNH NỘI DUNG VÀ LỌC ---

            # Chỉ thêm vào danh sách nếu nó khớp với một ID cụ thể
            tasks_to_add.append({
                "id": str(uuid.uuid4()), # Luôn tạo ID duy nhất cho ứng dụng
                "title": custom_title,
                "description": custom_description,
                "due_date": custom_due_date,
                "priority": custom_priority,
                "status": custom_status
            })

        if tasks_to_add:
            current_tasks = load_tasks()
            current_tasks.extend(tasks_to_add) # Thêm các công việc đã biến đổi vào danh sách hiện có
            save_tasks(current_tasks)
            messagebox.showinfo("Thông báo", f"Đã tải và thêm {len(tasks_to_add)} công việc từ API thành công!")
            refresh_task_list()
        else:
            messagebox.showinfo("Thông báo", "Không có công việc nào được tải từ API theo điều kiện đã đặt.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Lỗi kết nối API", f"Không thể kết nối hoặc tải dữ liệu từ API: {e}")
    except json.JSONDecodeError:
        messagebox.showerror("Lỗi dữ liệu API", "Dữ liệu nhận được từ API không phải định dạng JSON hợp lệ.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi không mong muốn khi tải dữ liệu từ API: {e}")
# --- Khởi tạo ứng dụng GUI ---
init_data_file()
root = tk.Tk()
root.title("Quản Lý Công Việc Cá Nhân")
root.geometry("800x650") # Kích thước cửa sổ ban đầu
root.minsize(700, 550) # Đặt kích thước tối thiểu để tránh các thành phần quá nhỏ

# Cấu hình grid của cửa sổ chính (root) để các hàng và cột giãn nở
root.grid_rowconfigure(0, weight=0) # Hàng input form, không giãn
root.grid_rowconfigure(1, weight=0) # Hàng buttons, không giãn
root.grid_rowconfigure(2, weight=0) # Hàng filter/search, không giãn
root.grid_rowconfigure(3, weight=1) # Hàng Treeview, sẽ giãn nở theo chiều dọc
root.grid_columnconfigure(0, weight=1) # Cột chính, sẽ giãn nở theo chiều ngang


# --- Frame nhập liệu (frame_input) ---
frame_input = tk.Frame(root, padx=15, pady=15, bd=2, relief="groove")
frame_input.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

tk.Label(frame_input, text="Tiêu đề:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
entry_title = tk.Entry(frame_input, font=('Arial', 10)) # Bỏ width để nó tự giãn
entry_title.grid(row=0, column=1, padx=5, pady=5, sticky="ew") # Rất quan trọng: sticky="ew"

tk.Label(frame_input, text="Mô tả:", font=('Arial', 10, 'bold')).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
entry_description = tk.Text(frame_input, height=4, font=('Arial', 10)) # Bỏ width
entry_description.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

tk.Label(frame_input, text="Ngày hết hạn (dd/mm/yyyy):", font=('Arial', 10, 'bold')).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
entry_due_date = tk.Entry(frame_input, font=('Arial', 10)) # Bỏ width
entry_due_date.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

tk.Label(frame_input, text="Độ ưu tiên:", font=('Arial', 10, 'bold')).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
priority_var = tk.StringVar(value="Cao")
tk.Radiobutton(frame_input, text="Cao", variable=priority_var, value="Cao", font=('Arial', 10)).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
tk.Radiobutton(frame_input, text="Thấp", variable=priority_var, value="Thấp", font=('Arial', 10)).grid(row=3, column=1, padx=60, pady=5, sticky=tk.W)

tk.Label(frame_input, text="Trạng thái:", font=('Arial', 10, 'bold')).grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
status_var = tk.StringVar(value="Cần thực hiện")
status_options = ["Cần thực hiện", "Đang thực hiện", "Hoàn thành"]
status_menu = ttk.Combobox(frame_input, textvariable=status_var, values=status_options, state="readonly", width=15, font=('Arial', 10))
status_menu.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
status_menu.set("Cần thực hiện")

# Cấu hình các cột của frame_input để giãn nở. Cột 1 (chứa Entry, Text, Combobox) sẽ giãn nở.
frame_input.grid_columnconfigure(0, weight=0) # Cột label, không giãn
frame_input.grid_columnconfigure(1, weight=1) # Cột input, giãn


# --- Frame nút chức năng (frame_buttons) ---
frame_buttons = tk.Frame(root, padx=15, pady=10)
frame_buttons.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

button_add = tk.Button(frame_buttons, text="Thêm", command=add_task, font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white')
button_add.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5) # Sử dụng pack thay vì grid để các nút tự cân bằng

button_edit = tk.Button(frame_buttons, text="Chỉnh sửa", command=edit_task, font=('Arial', 10, 'bold'), bg='#2196F3', fg='white')
button_edit.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)

button_delete = tk.Button(frame_buttons, text="Xóa", command=delete_task, font=('Arial', 10, 'bold'), bg='#F44336', fg='white')
button_delete.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)

button_clear = tk.Button(frame_buttons, text="Xóa Form", command=clear_entries, font=('Arial', 10), bg='#FFC107', fg='black')
button_clear.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)

button_fetch_api = tk.Button(frame_buttons, text="Tải từ API", command=fetch_and_add_from_api, font=('Arial', 10), bg='#9C27B0', fg='white')
button_fetch_api.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)

button_delete_all = tk.Button(frame_buttons, text="Xóa Tất Cả", command=delete_all_tasks, font=('Arial', 10, 'bold'), bg='#607D8B', fg='white')
button_delete_all.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)


# --- Frame tìm kiếm và lọc (frame_filter) ---
frame_filter = tk.Frame(root, padx=15, pady=10, bd=2, relief="sunken")
frame_filter.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

# Cấu hình grid_columnconfigure cho frame_filter
# Cột 1 (chứa search_entry) sẽ giãn nở nhiều nhất
frame_filter.grid_columnconfigure(0, weight=0) # Label "Tìm kiếm"
frame_filter.grid_columnconfigure(1, weight=5) # **Cột của search_entry, cho weight rất cao**
frame_filter.grid_columnconfigure(2, weight=0) # Label "Lọc ưu tiên"
frame_filter.grid_columnconfigure(3, weight=1) # Combobox Lọc ưu tiên
frame_filter.grid_columnconfigure(4, weight=0) # Label "Lọc trạng thái"
frame_filter.grid_columnconfigure(5, weight=1) # Combobox Lọc trạng thái
frame_filter.grid_columnconfigure(6, weight=1) # Một cột trống cuối cùng để hấp thụ không gian


tk.Label(frame_filter, text="Tìm kiếm:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
search_entry = tk.Entry(frame_filter, font=('Arial', 10)) # Bỏ width để nó tự giãn theo cột
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew") # Rất quan trọng: sticky="ew"
search_entry.bind("<KeyRelease>", lambda event: refresh_task_list())

tk.Label(frame_filter, text="Lọc ưu tiên:", font=('Arial', 10, 'bold')).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
filter_priority_var = tk.StringVar(value="Tất cả")
filter_priority_options = ["Tất cả", "Cao", "Thấp"]
filter_priority_menu = ttk.Combobox(frame_filter, textvariable=filter_priority_var, values=filter_priority_options, state="readonly", font=('Arial', 10)) # Bỏ width
filter_priority_menu.grid(row=0, column=3, padx=5, pady=5, sticky="ew") # Sticky "ew" để Combobox cũng giãn nhẹ
filter_priority_menu.bind("<<ComboboxSelected>>", lambda event: refresh_task_list())

tk.Label(frame_filter, text="Lọc trạng thái:", font=('Arial', 10, 'bold')).grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
filter_status_var = tk.StringVar(value="Tất cả")
filter_status_options = ["Tất cả", "Cần thực hiện", "Đang thực hiện", "Hoàn thành"]
filter_status_menu = ttk.Combobox(frame_filter, textvariable=filter_status_var, values=filter_status_options, state="readonly", font=('Arial', 10)) # Bỏ width
filter_status_menu.grid(row=0, column=5, padx=5, pady=5, sticky="ew") # Sticky "ew" để Combobox cũng giãn nhẹ
filter_status_menu.bind("<<ComboboxSelected>>", lambda event: refresh_task_list())


# --- Frame hiển thị danh sách công việc (Treeview) ---
frame_tasks = tk.Frame(root, padx=10, pady=10)
frame_tasks.grid(row=3, column=0, padx=10, pady=10, sticky="nsew") # Rất quan trọng: sticky="nsew" để giãn cả 4 hướng

# Định nghĩa các cột cho Treeview
columns = ('title', 'due_date', 'priority', 'status', 'description')
treeview_tasks = ttk.Treeview(frame_tasks, columns=columns, show='headings')

# Cấu hình tiêu đề và độ rộng của từng cột
treeview_tasks.heading('title', text='Tiêu đề', anchor=tk.W, command=lambda: treeview_sort_column(treeview_tasks, 'title', False))
treeview_tasks.column('title', width=180, anchor=tk.W, stretch=tk.YES)

treeview_tasks.heading('due_date', text='Ngày hết hạn', anchor=tk.W, command=lambda: treeview_sort_column(treeview_tasks, 'due_date', False))
treeview_tasks.column('due_date', width=100, anchor=tk.CENTER)

treeview_tasks.heading('priority', text='Ưu tiên', anchor=tk.W, command=lambda: treeview_sort_column(treeview_tasks, 'priority', False))
treeview_tasks.column('priority', width=80, anchor=tk.CENTER)

treeview_tasks.heading('status', text='Trạng thái', anchor=tk.W, command=lambda: treeview_sort_column(treeview_tasks, 'status', False))
treeview_tasks.column('status', width=80, anchor=tk.CENTER)

treeview_tasks.heading('description', text='Mô tả', anchor=tk.W)
treeview_tasks.column('description', width=0, stretch=tk.NO) # Vẫn là cột ẩn

treeview_tasks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Thanh cuộn cho Treeview
scrollbar_y = ttk.Scrollbar(frame_tasks, orient=tk.VERTICAL, command=treeview_tasks.yview)
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
treeview_tasks.configure(yscrollcommand=scrollbar_y.set)

# Ràng buộc sự kiện khi chọn một dòng trong Treeview
treeview_tasks.bind('<<TreeviewSelect>>', show_task_details)

# Định nghĩa Style cho Treeview (màu sắc)
style = ttk.Style()
style.configure("Treeview", rowheight=25)
style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
style.map("Treeview", background=[('selected', '#B0D7FF')])

# Định nghĩa tags cho màu sắc hàng
treeview_tasks.tag_configure("high_priority", background="#FFEBEE", foreground="#E53935")
treeview_tasks.tag_configure("low_priority", background="#E3F2FD", foreground="#2196F3")
treeview_tasks.tag_configure("done_task", background="#E8F5E9", foreground="#4CAF50")

# Làm mới danh sách công việc khi khởi động
refresh_task_list()

# Chạy ứng dụng
root.mainloop()