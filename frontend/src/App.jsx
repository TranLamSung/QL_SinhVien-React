import React, { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { logout } from "./store/authSlice";
import { authService, studentService } from "./services/api";
import LoginScreen from "./components/LoginScreen";
import AddStudentForm from "./components/AddStudentForm";
import FilterBar from "./components/FilterBar";
import StudentTable from "./components/StudentTable";
import ClassManager from "./components/ClassManger";
import { useDebounce } from "./components/useDebounce";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function App() {
    const dispatch = useDispatch();

    const { isLoggedIn, username } = useSelector((state) => state.auth);

    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("all");
    const [page, setPage] = useState(1);
    const debouncedSearch = useDebounce(search, 500);
    const [totalPages, setTotalPages] = useState(1);
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [editingStudent, setEditingStudent] = useState(null);

    useEffect(() => {
        if (!isLoggedIn) return;

        setLoading(true);
        studentService
            .getStudents(debouncedSearch, status, page)
            .then((res) => {
                const fetchedStudents = res.data.students || [];
                const fetchedTotalPages = res.data.total_pages || 1;

                if (page > fetchedTotalPages && fetchedTotalPages > 0) {
                    setPage(fetchedTotalPages); // Ép ứng dụng quay về trang trước đó
                } else {
                    setStudents(fetchedStudents);
                    setTotalPages(fetchedTotalPages);
                }
            })
            .catch((err) => {
                console.error("Lỗi tải danh sách sinh viên:", err);
            })
            .finally(() => {
                setLoading(false);
            });
    }, [isLoggedIn, debouncedSearch, status, page, refreshTrigger]);

    useEffect(() => {
        setPage(1);
    }, [debouncedSearch, status]);

    return (
        <div className="container py-4">
            <div className="d-flex justify-content-between align-items-center mb-4 p-3 bg-white rounded shadow-sm border">
                <h2 className="mb-0 fw-bold text-dark">
                    🎓 HỆ THỐNG QUẢN LÝ SINH VIÊN V3
                </h2>
                {isLoggedIn && (
                    <div className="d-flex align-items-center gap-3">
                        <span className="fw-bold text-secondary">
                            Xin chào,{" "}
                            <span className="text-primary">{username}</span>!
                        </span>
                        <button
                            className="btn btn-sm btn-danger fw-bold shadow-sm"
                            onClick={() => {
                                authService.logout().then(() => {
                                    dispatch(logout());
                                });
                            }}
                        >
                            Đăng xuất 🔒
                        </button>
                    </div>
                )}
            </div>

            {!isLoggedIn ? (
                <LoginScreen />
            ) : (
                <>
                    <AddStudentForm
                        onStudentAdded={() => setRefreshTrigger((p) => p + 1)}
                        editingStudent={editingStudent}
                        clearEdit={() => setEditingStudent(null)}
                        refreshTrigger={refreshTrigger}
                    />
                    <ClassManager
                        onClassDeleted={() => setRefreshTrigger((p) => p + 1)}
                        refreshTrigger={refreshTrigger}
                    />
                    {/* 🌟 THAY THẾ KHỐI NÚT BẤM FILE TRONG FILE APP.JSX: */}
                    <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mb-1">
                        <div className="flex-grow-1">
                            <FilterBar
                                search={search}
                                setSearch={setSearch}
                                status={status}
                                setStatus={setStatus}
                            />
                        </div>

                        {/* CỤM TÍNH NĂNG EXCEL (CHỈ CHO ADMIN) */}
                        <div
                            className="d-flex gap-2 align-items-center"
                            style={{ marginBottom: "16px" }}
                        >
                            {/* Nút 1: Xuất Excel (Giữ nguyên logic cũ) */}
                            <button
                                className="btn btn-outline-success fw-bold p-3 shadow-sm"
                                onClick={() => {
                                    toast.info(
                                        "⏳ Hệ thống đang khởi tạo file Excel...",
                                    );
                                    studentService
                                        .exportExcel()
                                        .then((response) => {
                                            const blob = new Blob(
                                                [response.data],
                                                {
                                                    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                },
                                            );
                                            const url =
                                                window.URL.createObjectURL(
                                                    blob,
                                                );
                                            const link =
                                                document.createElement("a");
                                            link.href = url;
                                            link.setAttribute(
                                                "download",
                                                `Danh_Sach_Sinh_Vien_${new Date().toISOString().slice(0, 10)}.xlsx`,
                                            );
                                            document.body.appendChild(link);
                                            link.click();
                                            window.URL.revokeObjectURL(url);
                                            link.remove();
                                            toast.success(
                                                "🟢 Xuất file Excel thành công!",
                                            );
                                        })
                                        .catch(() =>
                                            toast.error(
                                                "❌ Xuất file thất bại!",
                                            ),
                                        );
                                }}
                            >
                                📥 Xuất Excel
                            </button>

                            {/* Nút 2: Nhập Excel hàng loạt (Nâng cấp mới) */}
                            <div className="position-relative">
                                <input
                                    type="file"
                                    accept=".xlsx, .xls"
                                    className="d-none"
                                    id="excel-upload-input"
                                    onChange={(e) => {
                                        const file = e.target.files[0];
                                        if (!file) return;

                                        const formData = new FormData();
                                        formData.append("file", file);

                                        toast.info(
                                            "⏳ Đang đọc và nạp dữ liệu từ file Excel...",
                                        );

                                        studentService
                                            .importExcel(formData)
                                            .then((res) => {
                                                toast.success(
                                                    `🟢 ${res.data.message}`,
                                                );
                                                // Reset input file để có thể chọn lại chính file đó lần sau
                                                e.target.value = "";
                                                // Kích hoạt load lại bảng sinh viên và sĩ số lớp học ngay lập tức!
                                                setRefreshTrigger((p) => p + 1);
                                            })
                                            .catch((err) => {
                                                console.error(err);
                                                toast.error(
                                                    `❌ Thất bại: ${err.response?.data?.error || "Định dạng file không hỗ trợ!"}`,
                                                );
                                                e.target.value = "";
                                            });
                                    }}
                                />
                                <label
                                    htmlFor="excel-upload-input"
                                    className="btn btn-success fw-bold p-3 shadow-sm mb-0 text-nowrap"
                                    style={{ cursor: "pointer" }}
                                >
                                    📤 Nhập File Excel
                                </label>
                            </div>
                        </div>
                    </div>
                    {loading ? (
                        <div className="text-center my-5">
                            <div
                                className="spinner-border text-primary"
                                role="status"
                            >
                                <span className="visually-hidden">
                                    Đang tải dữ liệu...
                                </span>
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
                        />
                    )}
                </>
            )}
            <ToastContainer />
        </div>
    );
}

export default App;
