import React from "react";
import { toast } from "react-toastify";

function StudentTable({ list, onDeleted, onEdit, currentPage, totalPages, setPage, forceLogout, userRole }) {
  

  const handleDelete = (id, name) => {
    const token = localStorage.getItem("token");

    if (!token) {
        forceLogout("🔒 Phiên làm việc đã hết hạn, vui lòng đăng nhập lại!");
        return;
      }

    if (window.confirm(`Xác nhận xóa sinh viên ${name}?`)) {
      fetch(`http://127.0.0.1:5000/api/delete/${id}`, { method: "DELETE",
        headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
       })
       .then(res => {
          if (!res.ok) {
          if (res.status === 401) {
            forceLogout("🔒 Phiên làm việc đã hết hạn, vui lòng đăng nhập lại!");
            throw new Error("Token hết hạn")
          }
          throw new Error("Thao tác thất bại!");
        }
        return res.json();
        })
        .then(() => {
          toast.success(`🗑️ Đã xóa thành công sinh viên ${name}!`);
          onDeleted(); 
        })
        .catch(err => {
          if (err.message !== "Token hết hạn") toast.error(`❌ Không thể xóa: ${err.message}`);;
        });
    }
  };

  return (
    <>
      <div className="table-responsive shadow-sm rounded border bg-white">
        <table className="table table-striped table-hover mb-0">
          <thead className="table-dark">
            <tr>
              <th>Họ tên</th><th>Tuổi</th><th>Điểm số</th><th>Lớp học</th><th>Kết quả</th><th className="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {list.length === 0 ? (
              <tr><td colSpan="6" className="text-center text-danger py-3">Không có dữ liệu sinh viên phù hợp!</td></tr>
            ) : (
              list.map(s => (
                <tr key={s.id}>
                  <td>{s.name}</td><td>{s.age}</td><td><strong>{s.score}</strong></td>
                  <td><span className="badge bg-info text-dark">{s.nameClass}</span></td>
                  <td>{s.score >= 5 ? <span className="badge bg-success">ĐẬU</span> : <span className="badge bg-danger">HỌC LẠI</span>}</td>
                  {userRole == "admin" && (
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