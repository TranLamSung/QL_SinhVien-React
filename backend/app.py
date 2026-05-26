from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS 
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
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