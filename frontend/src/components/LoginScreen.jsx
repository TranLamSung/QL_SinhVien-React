import React, { useState } from "react";

function LoginScreen({ onLoginSuccess }) {
  const [isLoginMode, setIsLoginMode] = useState(true);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    const url = isLoginMode
      ? "http://127.0.0.1:5000/api/login"
      : "http://127.0.0.1:5000/api/register";

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((data) => {
            throw new Error(data.error || "Thao tác thất bại!");
          });
        }
        return res.json();
      })
      .then((data) => {
        if (isLoginMode) {
          console.log("Dữ liệu Backend trả về:", data);
          localStorage.setItem("token", data.token)
          localStorage.setItem("username", data.username)
          localStorage.setItem("role", data.role)
          onLoginSuccess(data.username, data.role);
        } else {
          setSuccessMessage("🎉 Đăng ký tài khoản thành công! Hãy đăng nhập.");
          setIsLoginMode(true);
          setPassword("");
        }
      })
      .catch((err) => setError(err.message));
  };

  return (
    <div
      className="d-flex justify-content-center align-items-center"
      style={{ minHeight: "70vh" }}
    >
      <div
        className="card p-4 shadow border-0"
        style={{ width: "100%", maxWidth: "400px" }}
      >
        <div className="text-center mb-4">
          <span className="fs-1">{isLoginMode ? "🔐" : "📝"}</span>
          <h3 className="fw-bold text-primary mt-2">
            {isLoginMode ? "ĐĂNG NHẬP" : "ĐĂNG KÝ TÀI KHOẢN"}
          </h3>
          <p className="text-muted small">
            {isLoginMode
              ? "Vui lòng đăng nhập để vào hệ thống"
              : "Tạo tài khoản quản trị mới"}
          </p>
        </div>

        {error && <div className="alert alert-danger py-2 small">{error}</div>}

        {successMessage && (
          <div className="alert alert-success py-2 small">{successMessage}</div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label text-secondary small fw-bold">
              Tài khoản
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Nhập tên tài khoản..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="mb-4">
            <label className="form-label text-secondary small fw-bold">
              Mật khẩu
            </label>
            <input
              type="password"
              className="form-control"
              placeholder="Nhập mật khẩu..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-100 fw-bold py-2 shadow-sm mb-3"
          >
            {isLoginMode ? "ĐĂNG NHẬP" : "ĐĂNG KÝ NGAY"}
          </button>

          <div className="text-center">
            {isLoginMode ? (
              <p className="small text-muted mb-0">
                Chưa có tài khoản?{" "}
                <span
                  className="text-primary fw-bold"
                  style={{ cursor: "pointer", textDecoration: "underline" }}
                  onClick={() => {
                    setIsLoginMode(false);
                    setError("");
                    setSuccessMessage("");
                  }}
                >
                  Đăng ký tại đây
                </span>
              </p>
            ) : (
              <p className="small text-muted mb-0">
                Đã có tài khoản rồi?{" "}
                <span
                  className="text-primary fw-bold"
                  style={{ cursor: "pointer", textDecoration: "underline" }}
                  onClick={() => {
                    setIsLoginMode(true);
                    setError("");
                    setSuccessMessage("");
                  }}
                >
                  Quay lại Đăng nhập
                </span>
              </p>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

export default LoginScreen;
