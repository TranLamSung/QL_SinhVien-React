import React, { useState, useEffect } from "react";
import { useSelector } from "react-redux";
import { studentService } from "../services/api";
import { toast } from "react-toastify";

function AddStudentForm({ onStudentAdded, editingStudent, clearEdit, refreshTrigger }) {
  const userRole = useSelector(state => state.auth.role);
  const [formData, setFormData] = useState({ name: "", age: "", score: "", idClass: "" });
  const [classes, setClasses] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    studentService.getClasses()
      .then(res => setClasses(res.data || []))
      .catch(err => console.log("Lỗi lấy danh sách lớp: ", err))
  }, [refreshTrigger])

  useEffect(() => {
    if (editingStudent) {
      setFormData({ 
        name: editingStudent.name, 
        age: editingStudent.age, 
        score: editingStudent.score, 
        idClass: editingStudent.idClass || "" 
      });
    } else {
      setFormData({ name: "", age: "", score: "", idClass: "" });
    }
  }, [editingStudent]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const isEditing = editingStudent !== null;
    setIsSubmitting(true);

    const payload = {
      name: formData.name,
      age: parseInt(formData.age),
      score: parseFloat(formData.score), 
      idClass: formData.idClass ? parseInt(formData.idClass) : null
    };

    const action = isEditing
      ? studentService.updateStudent(editingStudent.id, payload)
      : studentService.addStudent(payload);

    action
      .then(() => {
        toast.success(isEditing ? "✏️ Cập nhật sinh viên thành công!" : "🟢 Thêm sinh viên thành công!");
        setFormData({ name: "", age: "", score: "", idClass: "" });
        if (isEditing) clearEdit();
        onStudentAdded();
      })
      .catch(err => {
        if (err.response && err.response.status !== 401) {
          toast.error(`❌ Thất bại: ${err.response.data?.error || "Lỗi hệ thống"}`);
        }
      })
      .finally(() => setIsSubmitting(false));
  };

  if (userRole !== "admin") return null;

  return (
    <div className="card shadow-sm mb-4 border-0">
      <div className="card-header bg-success text-white">
        <h5 className="mb-0 fw-bold">
          {editingStudent ? "✏️ Cập Nhật Thông Tin Sinh Viên" : "➕ Thêm Sinh Viên Mới"}
        </h5>
      </div>
      <div className="card-body bg-light rounded-bottom border border-top-0">
        <form onSubmit={handleSubmit} className="row g-2">
          <div className="col-md-3">
            <input type="text" className="form-control" placeholder="Họ tên" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
          </div>
          <div className="col-md-2">
            <input type="number" className="form-control" placeholder="Tuổi" value={formData.age} onChange={e => setFormData({...formData, age: e.target.value})} required />
          </div>
          <div className="col-md-2">
            <input type="number" step="0.1" className="form-control" placeholder="Điểm" value={formData.score} onChange={e => setFormData({...formData, score: e.target.value})} required />
          </div>
          <div className="col-md-3">
            <select className="form-select" value={formData.idClass} onChange={e => setFormData({...formData, idClass: e.target.value})}>
              <option value="">-- Chọn lớp học --</option>
              {classes?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="col-md-2 d-flex gap-1">
            <button type="submit" className={`btn w-100 fw-bold ${editingStudent ? 'btn-warning' : 'btn-success'}`} disabled={isSubmitting}>
              {isSubmitting ? "Đang lưu..." : (editingStudent ? "Lưu" : "Thêm")}
            </button>
            {editingStudent && (
              <button type="button" className="btn btn-secondary" onClick={clearEdit}>Hủy</button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddStudentForm;