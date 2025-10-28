import React from "react";
import { Link, useNavigate } from "react-router-dom";

const LOGO_URL = "/images/logorgb.png";

/* простая проверка авторизации, как у вас */
function isAuthenticated() {
  return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  const isAuth = isAuthenticated();

  return (
    <div className="fixed inset-0 flex flex-col w-full bg-gray-50 overflow-hidden">
      {/* Header (в тон вашему HeaderBar) */}
      <div className="fixed top-0 w-full border-b border-tau-primary/15 bg-white/95 backdrop-blur z-50">
        <div className="mx-auto max-w-2xl flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <img src={LOGO_URL} alt="TAU Library" className="h-8 w-8 rounded-lg object-contain" />
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold text-tau-primary">TAU — LibraryBot</span>
              <span className="text-xs text-gray-600">Поиск по библиотеке и умные рекомендации</span>
            </div>
          </div>

          <div className="flex gap-2 items-center">
            {isAuth ? (
              <>
                <button
                  onClick={() => navigate("/profile")}
                  className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
                >
                  Профиль
                </button>
                <Link
                  to="/app"
                  className="text-xs sm:text-sm px-3 py-1.5 rounded-xl bg-tau-primary text-white hover:bg-tau-hover transition"
                >
                  Домой
                </Link>

              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
                >
                  Войти
                </Link>
                <Link
                  to="/register"
                  className="text-xs sm:text-sm px-3 py-1.5 rounded-xl bg-tau-primary text-white hover:bg-tau-hover transition"
                >
                  Регистрация
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 pt-[72px] flex items-center justify-center px-4">
        <div className="mx-auto max-w-2xl w-full bg-gradient-to-b from-tau-primary/10 to-white border border-tau-primary/15 rounded-2xl shadow-sm p-6 text-center">
          <div className="flex justify-center mb-3">
            <img src={LOGO_URL} alt="TAU Library" className="h-12 w-12 rounded-xl object-contain" />
          </div>
          <h1 className="text-3xl font-semibold text-tau-primary tracking-tight">404</h1>
          <p className="mt-2 text-gray-700">
            Кажется, такой страницы нет. Проверьте адрес или вернитесь на главную.
          </p>

          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            <Link
              to="/app"
              className="px-4 py-2 rounded-xl bg-tau-primary hover:bg-tau-hover text-white transition text-sm"
            >
              На главную
            </Link>
          </div>

          <p className="mt-4 text-xs text-gray-500">
            Подсказка: попробуйте запрос «сетевые технологии Таненбаум» или «книги по управлению проектами».
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
