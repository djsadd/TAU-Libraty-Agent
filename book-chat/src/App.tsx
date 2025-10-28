// src/main.tsx или src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ProtectedRoute, PublicOnlyRoute } from "./routes/guards";
import RecommendationsPage from "./pages/RecommendationsPage";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { ChatBox } from "./components/ChatBox";
import { ProfilePage } from "./pages/profile";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
      {/* Публичные только для НЕавторизованных */}
      <Route element={<PublicOnlyRoute redirectTo="/app" />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
    </Route>
    <Route element={<ProtectedRoute redirectTo="/login" />}>
        <Route path="/app" element={<ChatBox />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
    </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
