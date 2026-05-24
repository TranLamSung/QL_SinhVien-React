import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";

function AddStudentForm({ onStudentAdded, editingStudent, clearEdit, forceLogout, userRole }) {
  const [formData, setFormData] = useState({ name: "", age: "", score: "", idClass: "" });
  const [classes, setClasses] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/classes").then(res => res.json()).then(data => setClasses(data || []));
  }, []);

  useEffect(() => {
    if (editingStudent) {
      setFormData({ name: editingStudent.name, age: editingStudent.age, score: editingStudent.score, idClass: editingStudent.idClass || "" });
    } else {
      setFormData({ name: "", age: "", score: "", idClass: "" });
    }
  }, [editingStudent]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const isEditing = editingStudent !== null;
    const url = isEditing ? `http://127.0.0.1:5000/api/update/${editingStudent.id}` : `http://127.0.0.1:5000/api/add_student`;

    const token = localStorage.getItem("token");

    if (!token) {
      forceLogout("🔒 Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại!");
      return;
    }

    setIsSubmitting(true);

    fetch(url, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        name: formData.name, age: parseInt(formData.age), score: parseFloat(formData.score),
        idClass: formData.idClass ? parseInt(formData.idClass) : null
      }),
    })
      .then(res => {
        if (!res.ok) {
          if (res.status === 401) {
            forceLogout("Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại")
            throw new Error("Token hết hạn")
          }
          throw new Error("Thao tác thất bại!");
        }
        return res.json();
      })
      .then(() => {
        if (isEditing) {
          toast.success("📝 Cập nhật thông tin sinh viên thành công!");
        }
        else {
          toast.success("🎉 Thêm sinh viên mới thành công!");
        }
        setFormData({ name: "", age: "", score: "", idClass: "" });
        if (isEditing) clearEdit();
        onStudentAdded();
      })
      .catch(err => {
        if (err.message !== "Token hết hạn") toast.error(`❌ Lỗi: ${err.message}`);
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  };

  if (userRole !== "admin") return null

  return (
    <div className={`card shadow-sm mb-4 border-0 ${editingStudent ? 'border-start border-warning border-4' : ''}`}>
      <div className={`card-header text-white ${editingStudent ? 'bg-warning text-dark' : 'bg-primary'}`}>
        <h5 className="mb-0 fw-bold">{editingStudent ? `📝 Sửa Thông Tin: ${editingStudent.name}` : "✨ Thêm Sinh Viên Mới"}</h5>
      </div>
      <div className="card-body bg-light rounded-bottom border border-top-0">
        <form onSubmit={handleSubmit} className="row g-2">
          <div className="col-md-3"><input type="text" className="form-control" placeholder="Họ tên" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required /></div>
          <div className="col-md-2"><input type="number" className="form-control" placeholder="Tuổi" value={formData.age} onChange={e => setFormData({...formData, age: e.target.value})} required /></div>
          <div className="col-md-2"><input type="number" step="0.1" className="form-control" placeholder="Điểm" value={formData.score} onChange={e => setFormData({...formData, score: e.target.value})} required /></div>
          <div className="col-md-3">
            <select className="form-select" value={formData.idClass} onChange={e => setFormData({...formData, idClass: e.target.value})}>
              <option value="">-- Chọn lớp học --</option>
              {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="col-md-2 d-flex gap-1">
            <button type="submit" className={`btn w-100 fw-bold ${editingStudent ? 'btn-warning' : 'btn-success'}`}>{editingStudent ? "Lưu" : "Thêm"}</button>
            {editingStudent && <button type="button" className="btn btn-secondary" onClick={clearEdit}>Hủy</button>}
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddStudentForm;