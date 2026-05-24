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

# Cấu hình CORS không cần credentials cho JWT
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# =========================================================================
# 1. ĐỊNH NGHĨA CƠ SỞ DỮ LIỆU (MODELS)
# =========================================================================

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="giao_vien")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    students = db.relationship("Student", backref="current_class", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "student_count": len(self.students)}
    
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    idClass = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True)

def init_sample_data():
    if not User.query.first():
        # Tài khoản admin xịn
        admin = User(username="admin", role="admin")
        admin.set_password("admin")
        
        # Tài khoản giáo viên bị giới hạn quyền
        giao_vien = User(username="gv1", role="giao_vien")
        giao_vien.set_password("gv123")
        
        db.session.add_all([admin, giao_vien])
        db.session.commit()
        
    if not Class.query.first():
        cntt = Class(name="Công nghệ thông tin")
        ktdt = Class(name="Kinh tế đầu tư")
        nna = Class(name="Ngôn ngữ Anh")
        db.session.add_all([cntt, ktdt, nna])
        db.session.commit()

        list_students = [
            Student(name="Nguyễn Văn A", age=20, score=8.5, idClass=cntt.id),
            Student(name="Trần Thị B", age=21, score=4.2, idClass=cntt.id),
            Student(name="Lê Văn C", age=19, score=7.0, idClass=ktdt.id),
            Student(name="Phạm Văn D", age=22, score=3.0, idClass=nna.id),
            Student(name="Hoàng Văn E", age=20, score=6.5, idClass=None)
        ]
        db.session.add_all(list_students)
        db.session.commit()

# =========================================================================
# 2. XÂY DỰNG DECORATOR XÁC THỰC JWT
# =========================================================================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            header_parts = auth_header.split(" ")
            if len(header_parts) == 2 and header_parts[0] == "Bearer":
                token = header_parts[1]
        
        if not token:
            return jsonify({"error": "Token không hợp lệ hoặc bị thiếu!"}), 401

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

            if data.get("role") != "admin":
                return jsonify({"error": "Bạn không có quyền thực hiện hành động này!"}), 403
                
            current_user_id = data["user_id"]
        except:
            return jsonify({"error": "Xác thực thất bại!"}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated


# =========================================================================
# 3. XÂY DỰNG CÁC ROUTE API THUẦN JSON
# =========================================================================

# --- API 1: Đăng ký tài khoản ---
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or request.form
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu tài khoản hoặc mật khẩu"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Tài khoản đã tồn tại"}), 400

    new_user = User(username=username)
    new_user.set_password(password) 
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Đăng ký thành công!"}), 201

# --- API 2: Đăng nhập hệ thống (Cấp JWT Token) ---
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or request.form
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role" : user.role ,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=60)
        }

        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        
        return jsonify({
            "logged_in": True,
            "username": user.username,
            "role" : user.role ,
            "token": token
        }), 200
        
    return jsonify({"error": "Sai tài khoản hoặc mật khẩu!"}), 401

# --- API 3: Lấy danh sách lớp học ---
@app.route("/api/classes", methods=["GET"])
def get_classes():
    classes = Class.query.all()
    return jsonify([c.to_dict() for c in classes]), 200

# --- API 4: Lấy danh sách sinh viên (Có Tìm kiếm, Lọc kết quả, Phân trang) ---
@app.route("/api/students", methods=["GET"])
def get_students():
    search = request.args.get("search", "")    
    status = request.args.get("status", "all")   
    page = int(request.args.get("page", 1))      
    per_page = 3  

    query = Student.query
    
    if search:
        query = query.filter(Student.name.like(f"%{search}%"))
        
    if status == "pass":
        query = query.filter(Student.score >= 5.0)
    elif status == "fail":
        query = query.filter(Student.score < 5.0)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    students_list = [{
        "id": s.id, 
        "name": s.name, 
        "age": s.age, 
        "score": s.score, 
        "idClass": s.idClass,
        "nameClass": s.current_class.name if s.current_class else "Chưa xếp lớp"
    } for s in paginated.items]

    return jsonify({
        "students": students_list,
        "total_pages": paginated.pages,
        "current_page": paginated.page
    }), 200

# --- API 5: Thêm mới sinh viên (Đã bảo vệ bằng JWT) ---
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

# --- API 6: Cập nhật thông tin sinh viên (Đã bảo vệ bằng JWT) ---
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
# CHẠY ỨNG DỤNG FLASK SERVER
# =========================================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()         
        init_sample_data()      
    app.run(debug=True, port=5000)