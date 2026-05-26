import React, { useState, useEffect } from "react";
import { useSelector } from "react-redux";
import { studentService } from "../services/api";
import { toast } from "react-toastify";

function ClassManger({ onClassDeleted, refreshTrigger }) {
  const userRole = useSelector(state => state.auth.role);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newClassName, setNewClassName] = useState("");

  const loadClasses = () => {
    setLoading(true);
    studentService.getClassesManage()
      .then((res) => setClasses(res.data || []))
      .catch((err) => console.error("Lỗi tải danh mục lớp:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (userRole === "admin") {
      loadClasses();
    }
  }, [userRole, refreshTrigger]);

  const handleAddClass = (e) => {
    e.preventDefault();
    if (!newClassName.trim()) return;

    studentService.addClass(newClassName.trim())
      .then((res) => {
        toast.success(res.data?.message || "Thêm lớp học thành công!");
        setNewClassName("");
        loadClasses();
        onClassDeleted();
      })
      .catch((err) => {
        toast.error(`❌ Lỗi: ${err.response?.data?.error || "Không thể tạo lớp mới"}`);
      });
  };

  const handleDeleteClass = (id, name, count) => {
    const confirmMsg = count > 0 
      ? `⚠️ CẢNH BÁO: Lớp [${name}] đang có ${count} sinh viên. Nếu xóa lớp, TOÀN BỘ sinh viên này sẽ bị xóa theo (Cascade Delete). Bạn vẫn muốn xóa chứ?`
      : `Xác nhận xóa lớp học [${name}]?`;

    if (window.confirm(confirmMsg)) {
      studentService.deleteClass(id)
        .then((res) => {
          toast.success(res.data?.message || "Xóa lớp thành công!");
          loadClasses();      
          onClassDeleted();   
        })
        .catch(err => {
          if (err.response && err.response.status !== 401) {
            toast.error(`❌ Lỗi: ${err.response.data?.error || "Không thể xóa lớp"}`);
          }
        });
    }
  };

  if (userRole !== "admin") return null;

  return (
    <div className="card shadow-sm mb-4 border-0">
      <div className="card-header bg-dark text-white d-flex justify-content-between align-items-center">
        <h5 className="mb-0 fw-bold">🗂️ Quản Lý Danh Mục Lớp Học</h5>
        <button className="btn btn-sm btn-outline-light" onClick={loadClasses} disabled={loading}>
          {loading ? "Đang tải..." : "🔄 Làm mới"}
        </button>
      </div>
      <div className="card-body bg-light rounded-bottom border border-top-0 p-3">
        
        <form onSubmit={handleAddClass} className="row g-2 mb-3">
          <div className="col-md-9">
            <input type="text" className="form-control" placeholder="Nhập tên lớp học mới..." value={newClassName} onChange={(e) => setNewClassName(e.target.value)} required />
          </div>
          <div className="col-md-3">
            <button type="submit" className="btn btn-primary w-100 fw-bold">➕ Tạo lớp</button>
          </div>
        </form>

        <div className="row g-2">
          {classes.map((c) => (
            <div className="col-md-4" key={c.id}>
              <div className="p-2 bg-white rounded border d-flex justify-content-between align-items-center">
                <div>
                  <strong className="text-secondary">{c.name}</strong>
                  <div className="small text-muted">Sĩ số: <span className="badge bg-secondary">{c.student_count} SV</span></div>
                </div>
                <button 
                  className="btn btn-sm btn-outline-danger py-1 px-2"
                  onClick={() => handleDeleteClass(c.id, c.name, c.student_count)}
                >
                  🗑️ Xóa
                </button>
              </div>
            </div>
          ))}
          {classes.length === 0 && <p className="text-center text-muted my-2 small">Chưa có lớp học nào trên hệ thống.</p>}
        </div>
      </div>
    </div>
  );
}

export default ClassManger;