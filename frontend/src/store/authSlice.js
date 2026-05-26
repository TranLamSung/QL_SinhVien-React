import { createSlice } from "@reduxjs/toolkit";

const initialToken = localStorage.getItem("token");
const savedUsername = localStorage.getItem("username");
const savedRole = localStorage.getItem("role");

const initialState = {
  isLoggedIn: !!initialToken,
  token: initialToken || null,
  username: savedUsername || "",
  role: savedRole || "",
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    loginSuccess: (state, action) => {
      const { token, username, role } = action.payload;
      state.isLoggedIn = true;
      state.token = token;
      state.username = username;
      state.role = role;

      localStorage.setItem("token", token);
      localStorage.setItem("username", username);
      localStorage.setItem("role", role);
    },
    logout: (state) => {
      state.isLoggedIn = false;
      state.token = null;
      state.username = "";
      state.role = "";

      localStorage.removeItem("token");
      localStorage.removeItem("username");
      localStorage.removeItem("role");
    },
  },
});

export const { loginSuccess, logout } = authSlice.actions;
export default authSlice.reducer;