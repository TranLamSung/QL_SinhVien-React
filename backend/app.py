from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS 
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io
import os 
import jwt
import datetime


app = Flask(__name__)

# Chuỗi bí mật ký Token
app.config["SECRET_KEY"] = "chuoi_bi_mat_sieu_cap_cua_ban_nam_2026"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "qlsv.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Cho phép truyền Cookie giữa Frontend và Backend kèm thuộc tính supports_credentials=True
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# =========================================================================
# 1. ĐỊNH NGHĨA CƠ SỞ DỮ LIỆU (MODELS)
# =========================================================================

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user") # Quyền hạn: admin hoặc user

class Class(db.Model):
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    students = db.relationship("Student", backref="class_ref", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "student_count": len(self.students)
        }

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    idClass = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "score": self.score,
            "idClass": self.idClass,
            "nameClass": self.class_ref.name if self.class_ref else "Chưa xếp lớp"
        }

# =========================================================================
# 2. BỘ KIỂM TRA QUYỀN TRUY CẬP (MIDDLEWARE DECORATORS)
# =========================================================================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split(" ")
            if len(parts) == 2:
                token = parts[1]
        
        if not token:
            return jsonify({"error": "Quyền truy cập bị từ chối! Thiếu Token."}), 401
        
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            if data.get("role") != "admin":
                return jsonify({"error": "Bạn không có quyền thực hiện hành động này!"}), 403
            current_user_id = data.get("user_id")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token đã hết hạn!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token không hợp lệ!"}), 401
            
        return f(current_user_id, *args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split(" ")
            if len(parts) == 2:
                token = parts[1]
                
        if not token:
            return jsonify({"error": "Vui lòng đăng nhập!"}), 401
            
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user_id = data.get("user_id")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token đã hết hạn!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token không hợp lệ!"}), 401
            
        return f(current_user_id, *args, **kwargs)
    return decorated

# =========================================================================
# 3. HỆ THỐNG APIS ĐIỀU HƯỚNG CHÍNH (ROUTES)
# =========================================================================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Tài khoản và mật khẩu không được trống!"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Tài khoản đã tồn tại trên hệ thống!"}), 400

    # Tài khoản đầu tiên đăng ký tự động làm Admin, các tài khoản sau là User phổ thông
    is_first_user = User.query.count() == 0
    role = "admin" if is_first_user else "user"

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": f"Đăng ký tài khoản {role} thành công!"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get("username")).first()

    if not user or not check_password_hash(user.password_hash, data.get("password")):
        return jsonify({"error": "Sai tài khoản hoặc mật khẩu!"}), 401

    # Tạo Access Token (Hiệu lực ngắn - 15 phút) gửi về cho Frontend lưu trong Store
    access_token = jwt.encode({
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }, app.config["SECRET_KEY"], algorithm="HS256")

    # Tạo Refresh Token (Hiệu lực dài - 7 ngày) bọc kín đóng vào HTTP-Only Cookie an toàn bảo mật
    refresh_token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config["SECRET_KEY"], algorithm="HS256")

    response = jsonify({
        "token": access_token,
        "username": user.username,
        "role": user.role
    })
    
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,  # Chuyển sang True nếu dùng cổng HTTPS thực tế
        samesite="Lax",
        max_age=7 * 24 * 60 * 60 # 7 ngày quy đổi ra giây
    )
    return response, 200


@app.route("/api/refresh", methods=["POST"])
def refresh():
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Thiếu phiên làm việc dài hạn, vui lòng đăng nhập!"}), 401

    try:
        data = jwt.decode(refresh_token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user = User.query.get(data.get("user_id"))
        if not user:
            return jsonify({"error": "Người dùng không tồn tại!"}), 401

        # Cấp Access Token mới
        new_access_token = jwt.encode({
            "user_id": user.id,
            "role": user.role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }, app.config["SECRET_KEY"], algorithm="HS256")

        return jsonify({"token": new_access_token}), 200
    except:
        return jsonify({"error": "Phiên làm việc hết hạn!"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    response = jsonify({"message": "Đã đăng xuất hoàn toàn khỏi hệ thống!"})
    response.delete_cookie("refresh_token")
    return response, 200


@app.route("/api/classes", methods=["GET"])
@login_required
def get_classes(current_user_id):
    classes = Class.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in classes]), 200


@app.route("/api/classes_manage", methods=["GET"])
@admin_required
def get_classes_manage(current_user_id):
    try:
        classes = Class.query.all()
        return jsonify([c.to_dict() for c in classes]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/add_class", methods=["POST"])
@admin_required
def add_class(current_user_id):
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "Tên lớp học không được để trống!"}), 400
    if Class.query.filter_by(name=name).first():
        return jsonify({"error": "Tên lớp học này đã tồn tại!"}), 400

    new_class = Class(name=name)
    db.session.add(new_class)
    db.session.commit()
    return jsonify({"message": "Thêm lớp học thành công!", "class": new_class.to_dict()}), 201


@app.route("/api/delete_class/<int:id>", methods=["DELETE"])
@admin_required
def delete_class(current_user_id, id):
    target_class = Class.query.get_or_404(id)
    db.session.delete(target_class)
    db.session.commit()
    return jsonify({"message": f"Đã xóa lớp {target_class.name} thành công!"}), 200


@app.route("/api/students", methods=["GET"])
@login_required
def get_students(current_user_id):
    search = request.args.get("search", "")
    status = request.args.get("status", "all")
    page = int(request.args.get("page", 1))
    per_page = 5

    query = Student.query
    if search:
        query = query.filter(Student.name.like(f"%{search}%"))

    if status == "pass":
        query = query.filter(Student.score >= 5.0)
    elif status == "fail":
        query = query.filter(Student.score < 5.0)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "students": [s.to_dict() for s in paginated.items],
        "total_pages": paginated.pages,
        "current_page": page
    }), 200


@app.route("/api/add_student", methods=["POST"])
@admin_required
def add_student(current_user_id):
    data = request.get_json() or {}
    new_student = Student(
        name=data.get("name"),
        age=int(data.get("age")),
        score=float(data.get("score")),
        idClass=int(data.get("idClass")) if data.get("idClass") else None
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"message": "Thêm sinh viên thành công!"}), 201


@app.route("/api/update/<int:id>", methods=["POST"])
@admin_required
def update_student(current_user_id, id):
    student = Student.query.get_or_404(id)
    data = request.get_json() or {}
    
    student.name = data.get("name", student.name)
    student.age = int(data.get("age", student.age))
    student.score = float(data.get("score", student.score))
    
    idClass = data.get("idClass")
    student.idClass = int(idClass) if idClass else None
    
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công!"}), 200


# --- API 7: Xóa sinh viên (Đã bảo vệ bằng JWT) ---
@app.route("/api/delete/<int:id>", methods=["DELETE"])
@admin_required
def delete_student(current_user_id, id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Xóa thành công!"}), 200

# --- API 8: Xuất toàn bộ danh sách sinh viên ra file Excel (Bảo vệ bằng Quyền Admin) ---
@app.route("/api/export_excel", methods=["GET"])
@admin_required
def export_excel(current_user_id):
    try:
        # 1. Lấy toàn bộ danh sách sinh viên từ Database
        students = Student.query.all()
        
        # 2. Khởi tạo một file Excel mới
        wb = Workbook()
        ws = wb.active
        ws.title = "Danh sách Sinh viên"
        
        # 3. Định nghĩa các kiểu trang trí (Styles)
        font_title = Font(name="Arial", size=14, bold=True, color="FFFFFF")
        font_header = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        font_data = Font(name="Arial", size=11)
        
        fill_title = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        fill_header = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        
        border_thin = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        # 4. Tạo dòng tiêu đề lớn (Gộp từ cột A đến E)
        ws.merge_cells("A1:E1")
        ws["A1"] = "DANH SÁCH TỔNG HỢP SINH VIÊN TOÀN TRƯỜNG"
        ws["A1"].font = font_title
        ws["A1"].fill = fill_title
        ws["A1"].alignment = align_center
        ws.row_dimensions[1].height = 40
        
        # 5. Tạo hàng Tiêu đề các cột
        headers = ["STT", "Họ tên Sinh viên", "Tuổi", "Điểm số", "Lớp học"]
        ws.append([]) # Dòng 2 trống
        ws.append(headers) # Dòng 3 điền headers
        
        ws.row_dimensions[3].height = 25
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_num)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center
            cell.border = border_thin
            
        # 6. Đổ dữ liệu Sinh viên vào từ dòng số 4
        for idx, sv in enumerate(students, start=1):
            name_class = sv.class_ref.name if sv.class_ref else "Chưa xếp lớp"
            row_data = [idx, sv.name, sv.age, sv.score, name_class]
            ws.append(row_data)
            
            current_row = 3 + idx
            ws.row_dimensions[current_row].height = 20
            
            for col_num in range(1, 6):
                cell = ws.cell(row=current_row, column=col_num)
                cell.font = font_data
                cell.border = border_thin
                if col_num in [1, 3, 4]:
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left

        # 7. Tự động căn chỉnh độ rộng các cột (Tránh lỗi MergedCell)
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row == 1:
                    continue
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 5, 12)

        # 🌟 BƯỚC THAY ĐỔI QUAN TRỌNG: Ghi dữ liệu sạch tuyệt đối vào luồng Bytes
        excel_stream = io.BytesIO()
        wb.save(excel_stream)
        excel_stream.seek(0) # Đưa con trỏ đọc về vị trí xuất phát đầu tiên

        # Tạo tên file đính kèm
        file_name = f"Danh_Sach_Sinh_Vien_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 🌟 ÉP PHẢI TRẢ VỀ DẠNG SEND_FILE CHUẨN ĐỊNH DẠNG KHÔNG BỊ TRỘN LOG
        return send_file(
            excel_stream,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=file_name
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc()) # In chi tiết lỗi ra Terminal để debug nếu sập
        return jsonify({"error": f"Lỗi xuất Excel: {str(e)}"}), 500

# --- API 9: Nhập dữ liệu sinh viên hàng loạt từ file Excel (Bảo vệ bằng Quyền Admin) ---
@app.route("/api/import_excel", methods=["POST"])
@admin_required
def import_excel(current_user_id):
    try:
        # 1. Kiểm tra xem Frontend có gửi file lên không
        if "file" not in request.files:
            return jsonify({"error": "Không tìm thấy file tải lên!"}), 400
            
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Tên file trống!"}), 400
            
        # 🌟 ĐOẠN SỬA LỖI 500 CHÍ MẠNG: Đọc file an toàn sử dụng Workbook
        from openpyxl import load_workbook # Thêm dòng này ngay tại đây cho chắc chắn
        
        # Đọc trực tiếp file dữ liệu nhị phân gửi từ client lên
        wb = load_workbook(file, data_only=True) 
        ws = wb.active # Lấy Sheet hoạt động đầu tiên
        
        success_count = 0
        errors = []
        
        # 3. Duyệt qua từng dòng trong file Excel (Bắt đầu từ dòng số 4)
        for row_idx, row in enumerate(ws.iter_rows(min_row=4, values_only=True), start=4):
            if not row or row[1] is None:
                continue
                
            try:
                name = str(row[1]).strip()
                age = int(row[2])
                score = float(row[3])
                class_name = str(row[4]).strip() if row[4] is not None else ""
                
                # Tìm hoặc tạo ID lớp học dựa vào tên lớp
                id_class = None
                if class_name:
                    cls = Class.query.filter_by(name=class_name).first()
                    if cls:
                        id_class = cls.id
                    else:
                        new_cls = Class(name=class_name)
                        db.session.add(new_cls)
                        db.session.commit()
                        id_class = new_cls.id
                
                # 🌟 ĐOẠN KIỂM TRA TRÙNG LẶP DỮ LIỆU CHÍ MẠNG:
                # Tìm xem trong DB đã có sinh viên trùng cả Tên và Lớp học này chưa
                existing_student = Student.query.filter_by(name=name, idClass=id_class).first()
                
                if existing_student:
                    # TÌNH HUỐNG 1: Đã tồn tại -> Cập nhật thông tin mới nhất (Tuổi, Điểm)
                    existing_student.age = age
                    existing_student.score = score
                else:
                    # TÌNH HUỐNG 2: Chưa tồn tại -> Tiến hành thêm mới như bình thường
                    new_student = Student(
                        name=name,
                        age=age,
                        score=score,
                        idClass=id_class
                    )
                    db.session.add(new_student)
                    
                success_count += 1
                
            except Exception as row_error:
                errors.append(f"Dòng {row_idx}: {str(row_error)}")
                
        # 4. Lưu toàn bộ sinh viên hợp lệ vào Database
        if success_count > 0:
            db.session.commit()
            
        return jsonify({
            "message": f"Nhập dữ liệu thành công {success_count} sinh viên!",
            "errors": errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        # In chi tiết lỗi ra Terminal của Flask để dễ theo dõi
        import traceback
        print("LỖI IMPORT EXCEL CHI TIẾT:")
        print(traceback.format_exc())
        return jsonify({"error": f"Lỗi xử lý file Excel: {str(e)}"}), 500

# =========================================================================
# 4. HÀM KHỞI TẠO DỮ LIỆU MẪU RIÊNG BIỆT (SEED DATA FUNCTION)
# =========================================================================
def seed_data(app_instance, db_instance):
    """
    Hàm tự động kiểm tra và nạp dữ liệu mẫu vào cơ sở dữ liệu.
    Được tách riêng để dễ bảo trì, quản lý hoặc mở rộng sau này.
    """
    with app_instance.app_context():
        try:
            # 1. Tạo các bảng nếu hệ thống chưa có file qlsv.db
            db_instance.create_all()
            
            # 2. Nếu bảng User đã có dữ liệu -> Dừng lại luôn, không ghi đè dữ liệu cũ
            if User.query.count() > 0:
                return

            print("🌟 Đang tiến hành khởi tạo dữ liệu mẫu cho hệ thống...")
            
            # Khởi tạo Tài khoản hệ thống (Mật khẩu được mã hóa an toàn)
            admin_user = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="admin"
            )
            normal_user = User(
                username="user",
                password_hash=generate_password_hash("user123"),
                role="user"
            )
            db_instance.session.add(admin_user)
            db_instance.session.add(normal_user)
            
            # Khởi tạo Lớp học mẫu
            class_it = Class(name="Công nghệ thông tin K16")
            class_biz = Class(name="Quản trị kinh doanh K12")
            class_eng = Class(name="Ngôn ngữ Anh K14")
            db_instance.session.add_all([class_it, class_biz, class_eng])
            
            # Phải Commit tầng 1 để SQLite sinh ID tự động cho Lớp học, 
            # sau đó mới lấy ID này gắn cho Sinh viên ở tầng dưới được.
            db_instance.session.commit()
            
            # Khởi tạo Sinh viên mẫu với đầy đủ điểm số ĐẬU / HỌC LẠI
            sv1 = Student(name="Nguyễn Văn Anh", age=20, score=8.5, idClass=class_it.id)
            sv2 = Student(name="Trần Thị Bình", age=21, score=4.2, idClass=class_it.id)
            sv3 = Student(name="Lê Hoàng Cường", age=22, score=7.0, idClass=class_biz.id)
            sv4 = Student(name="Phạm Minh Đức", age=19, score=3.5, idClass=class_biz.id)
            sv5 = Student(name="Vũ Hoàng Yến", age=20, score=9.2, idClass=class_eng.id)
            
            db_instance.session.add_all([sv1, sv2, sv3, sv4, sv5])
            db_instance.session.commit()
            
            print("🟢 [SUCCESS] Khởi tạo dữ liệu mẫu thành công!")
            print("👉 Tài khoản Admin: admin / admin123")
            print("👉 Tài khoản User:  user / user123")
            
        except Exception as e:
            db_instance.session.rollback()
            print(f"❌ [ERROR] Lỗi không thể tạo dữ liệu mẫu: {str(e)}")


# =========================================================================
# 5. KHỞI CHẠY SERVER CHÍNH
# =========================================================================
if __name__ == "__main__":
    # Tự động gọi hàm tạo dữ liệu mẫu ngay khi bật Server lên
    seed_data(app, db)
    
    # Chạy Flask ở chế độ Debug, cổng 5000
    app.run(debug=True, port=5000)