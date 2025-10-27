// src/main.tsx или src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { ChatBox } from "./components/ChatBox";
import { ProfilePage } from "./pages/profile";


export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/app" element={<ChatBox />} />
        <Route path="*" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}
