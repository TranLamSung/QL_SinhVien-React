import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { loginSuccess } from "../store/authSlice";
import { authService } from "../services/api";

function LoginScreen() {
  const dispatch = useDispatch();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (isLoginMode) {
      authService.login(username, password)
        .then((res) => {
          dispatch(loginSuccess({
            token: res.data.token,
            username: res.data.username,
            role: res.data.role
          }));
        })
          .catch((err) => {
          setError(err.response?.data?.error || "Đăng nhập thất bại!");
        });
    } else {
      authService.register(username, password)
        .then((res) => {
          setSuccessMessage(res.data?.message || "Đăng ký thành công! Hãy chuyển về Đăng nhập.");
          setUsername("");
          setPassword("");
        })
        .catch((err) => {
          setError(err.response?.data?.error || "Đăng ký thất bại!");
        });
    }
  };

  return (
    <div className="row justify-content-center my-5">
      <div className="col-md-5">
        <div className="card shadow border-0 p-4 bg-white rounded">
          <h3 className="text-center fw-bold text-primary mb-4">
            {isLoginMode ? "🔑 ĐĂNG NHẬP HỆ THỐNG" : "📝 ĐĂNG KÝ TÀI KHOẢN"}
          </h3>

          {error && <div className="alert alert-danger py-2 text-center small fw-bold">{error}</div>}
          {successMessage && <div className="alert alert-success py-2 text-center small fw-bold">{successMessage}</div>}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label text-secondary small fw-bold">Tên tài khoản</label>
              <input type="text" className="form-control" placeholder="Nhập tên tài khoản..." value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div className="mb-4">
              <label className="form-label text-secondary small fw-bold">Mật khẩu</label>
              <input type="password" className="form-control" placeholder="Nhập mật khẩu..." value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>

            <button type="submit" className="btn btn-primary w-100 fw-bold py-2 shadow-sm mb-3">
              {isLoginMode ? "ĐĂNG NHẬP" : "ĐĂNG KÝ NGAY"}
            </button>

            <div className="text-center">
              {isLoginMode ? (
                <p className="small text-muted mb-0">
                  Chưa có tài khoản?{" "}
                  <span className="text-primary fw-bold" style={{ cursor: "pointer", textDecoration: "underline" }} onClick={() => { setIsLoginMode(false); setError(""); setSuccessMessage(""); }}>Đăng ký tại đây</span>
                </p>
              ) : (
                <p className="small text-muted mb-0">
                  Đã có tài khoản rồi?{" "}
                  <span className="text-primary fw-bold" style={{ cursor: "pointer", textDecoration: "underline" }} onClick={() => { setIsLoginMode(true); setError(""); setSuccessMessage(""); }}>Quay lại Đăng nhập</span>
                </p>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default LoginScreen;