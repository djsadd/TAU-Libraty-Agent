import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

function isAuthenticated() {
  return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

/** Закрытый маршрут: пускает только авторизованных, иначе редиректит на /login */
export const ProtectedRoute: React.FC<{ redirectTo?: string }> = ({ redirectTo = "/login" }) => {
  const location = useLocation();
  const allowed = isAuthenticated();

  if (!allowed) {
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }
  return <Outlet />;
};

/** Публичный-ONLY маршрут: пускает только НЕавторизованных, иначе уводит на /app */
export const PublicOnlyRoute: React.FC<{ redirectTo?: string }> = ({ redirectTo = "/app" }) => {
  const location = useLocation();
  const allowed = !isAuthenticated();

  if (!allowed) {
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }
  return <Outlet />;
};
