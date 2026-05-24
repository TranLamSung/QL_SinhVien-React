import React, { useState, useEffect } from "react";
import LoginScreen from "./components/LoginScreen";
import AddStudentForm from "./components/AddStudentForm";
import FilterBar from "./components/FilterBar";
import StudentTable from "./components/StudentTable";
import { useDebounce } from "./components/useDebounce";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";


function App() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("token");
    const savedUsername = localStorage.getItem("username");
    const savedRole = localStorage.getItem("role");

    return token && savedUsername && savedRole
      ? { logged_in: true, username: savedUsername, role: savedRole }
      : { logged_in: false, username: "", role: "" };
  });
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false); // 🌟 State quản lý trạng thái tải dữ liệu
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebounce(search, 500);
  const [totalPages, setTotalPages] = useState(1);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [editingStudent, setEditingStudent] = useState(null);

  const handleLogout = (message = "Đã đăng xuất hệ thống!") => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("role");

    setUser({ logged_in: false, username: "", role: "" });
    setStudents([]);
    toast.warn(message, { position: "top-right", autoClose: 3000 });
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedUsername = localStorage.getItem("username");

    if (token && savedUsername) {
      setUser({ logged_in: true, username: savedUsername });
    }
  }, []);

  useEffect(() => {
    if (!user.logged_in) return;
    setLoading(true);
    fetch(
      `http://127.0.0.1:5000/api/students?search=${debouncedSearch}&status=${status}&page=${page}`,
    )
      .then((res) => {
        if (res.status == 401) {
          handleLogout();
          throw new Error("Phiên làm việc đã hết hạn, vui lòng đăng nhập lại!");
        }
        return res.json();
      })
      .then((data) => {
        setStudents(data.students || []);
        setTotalPages(data.total_pages || 1);
      })
      .catch((err) => console.error("Lỗi tải sinh viên:", err))
      .finally(() => {
        setLoading(false); // 🌟 2. Tắt loading dù fetch thành công hay thất bại
      });
  }, [debouncedSearch, status, page, refreshTrigger, user.logged_in]);

  useEffect(() => {
    setPage(1);
  }, [search, status]);

  return (
    <div className="container mt-4" style={{ maxWidth: "950px" }}>
      <div className="d-flex justify-content-between align-items-center bg-white p-3 rounded shadow-sm border mb-4">
        <div>
          <h4 className="mb-0 text-primary fw-bold">
            🎓 PORTAL QUẢN LÝ SINH VIÊN
          </h4>
          <small className="text-muted">
            Hệ thống Full-stack React + Flask + SQLite
          </small>
        </div>
        {user.logged_in && (
          <div className="d-flex align-items-center gap-3">
            <span className="badge bg-success py-2 px-3 text-uppercase fs-6">
              Hi, {user.username}
            </span>
            <button
              className="btn btn-sm btn-danger fw-bold"
              onClick={() => handleLogout()}
            >
              Đăng xuất 🔒
            </button>
          </div>
        )}
      </div>

      {!user.logged_in ? (
        <LoginScreen
          onLoginSuccess={(name, role) => {
            console.log("React nhận được role từ LoginScreen:", role);
            setUser({ logged_in: true, username: name, role: role });
          }}
        />
      ) : (
        <>
          <AddStudentForm
            onStudentAdded={() => setRefreshTrigger((p) => p + 1)}
            editingStudent={editingStudent}
            clearEdit={() => setEditingStudent(null)}
            forceLogout={handleLogout}
            userRole={user?.role}
          />
          <FilterBar
            search={search}
            setSearch={setSearch}
            status={status}
            setStatus={setStatus}
          />
          {loading ? (
            <div className="text-center my-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Đang tải dữ liệu...</span>
              </div>
              <p className="mt-2 text-secondary">
                Chờ một chút, dữ liệu đang tải...
              </p>
            </div>
          ) : (
            <StudentTable
              list={students}
              onDeleted={() => setRefreshTrigger((p) => p + 1)}
              onEdit={(s) => setEditingStudent(s)}
              currentPage={page}
              totalPages={totalPages}
              setPage={setPage}
              forceLogout={handleLogout}
              userRole={user?.role}
            />
          )}
        </>
      )}
      <ToastContainer />
    </div>
  );
}

export default App;
