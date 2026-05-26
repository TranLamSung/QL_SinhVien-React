import React from "react";
import { useSelector } from "react-redux";
import { studentService } from "../services/api";
import { toast } from "react-toastify";

function StudentTable({ list, onDeleted, onEdit, currentPage, totalPages, setPage }) {
  const userRole = useSelector((state) => state.auth.role);

  const handleDelete = (id, name) => {
    if (window.confirm(`Xác nhận xóa sinh viên ${name}?`)) {
      studentService.deleteStudent(id)
        .then(() => {
          toast.success(`🗑️ Đã xóa thành công sinh viên ${name}!`);
          onDeleted(); 
        })
        .catch(err => {
          if (err.response && err.response.status !== 401) {
            toast.error(`❌ Không thể xóa: ${err.response.data?.error || "Lỗi chưa xác định"}`);
          }
        });
    }
  };

  return (
    <>
      <div className="table-responsive shadow-sm rounded border bg-white">
        <table className="table table-striped table-hover mb-0">
          <thead className="table-dark">
            <tr>
              <th>Họ tên</th><th>Tuổi</th><th>Điểm số</th><th>Lớp học</th><th>Kết quả</th>
              {userRole === "admin" && <th className="text-center">Thao tác</th>}
            </tr>
          </thead>
          <tbody>
            {list.length === 0 ? (
              <tr>
                <td colSpan={userRole === "admin" ? 6 : 5} className="text-center py-4 text-muted">
                  Không tìm thấy sinh viên nào tương ứng với bộ lọc.
                </td>
              </tr>
            ) : (
              list.map((s) => (
                <tr key={s.id} className="align-middle">
                  <td>{s.name}</td><td>{s.age}</td><td><strong>{s.score}</strong></td>
                  <td><span className="badge bg-info text-dark">{s.nameClass}</span></td>
                  <td>{s.score >= 5 ? <span className="badge bg-success">ĐẬU</span> : <span className="badge bg-danger">HỌC LẠI</span>}</td>
                  {userRole === "admin" && (
                    <td className="text-center">
                      <div className="btn-group gap-1">
                        <button className="btn btn-sm btn-warning" onClick={() => onEdit(s)}>✏️ Sửa</button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(s.id, s.name)}>🗑️ Xóa</button>
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <nav className="d-flex justify-content-center mt-3">
          <ul className="pagination shadow-sm">
            <button className="page-link" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>Trước</button>
            <span className="page-link bg-light text-dark fw-bold">Trang {currentPage} / {totalPages}</span>
            <button className="page-link" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>Sau</button>
          </ul>
        </nav>
      )}
    </>
  );
}

export default StudentTable;