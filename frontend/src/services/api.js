import axios from "axios";
import { store } from "../store";
import { loginSuccess, logout } from "../store/authSlice";

const api = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true
});

api.interceptors.request.use(
  (config) => {
    const token = store.getState().auth.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

let isRefreshing = false; 
let failedQueue = [];     

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response && 
      error.response.status === 401 && 
      !originalRequest._retry &&
      !originalRequest.url.includes("/login")) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const res = await axios.post("http://127.0.0.1:5000/api/refresh", {}, { withCredentials: true });
        const newToken = res.data.token;

        const savedUsername = localStorage.getItem("username") || "";
        const savedRole = localStorage.getItem("role") || "";
        
        store.dispatch(loginSuccess({
          token: newToken,
          username: savedUsername, 
          role: savedRole          
        }));

        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        if (store.getState().auth.isLoggedIn) {
          store.dispatch(logout());
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  login: (username, password) => api.post("/login", { username, password }),
  register: (username, password) => api.post("/register", { username, password }),
  logout: () => api.post("/logout"), 
};

export const studentService = {
  getClasses: () => api.get("/classes"),
  getClassesManage: () => api.get("/classes_manage"),
  addClass: (name) => api.post("/add_class", { name }),
  deleteClass: (id) => api.delete(`/delete_class/${id}`),
  getStudents: (search, status, page) => 
    api.get(`/students?search=${search}&status=${status}&page=${page}`),
  addStudent: (data) => api.post("/add_student", data),
  updateStudent: (id, data) => api.post(`/update/${id}`, data),
  deleteStudent: (id) => api.delete(`/delete/${id}`),
};