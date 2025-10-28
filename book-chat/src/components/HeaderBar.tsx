import React from "react";

const LOGO_URL = "/images/logorgb.png";

export const HeaderBar: React.FC<{
  isAuth: boolean;
  onLogout: () => void;
}> = ({ isAuth, onLogout }) => (
  <div className="fixed top-0 w-full border-b border-tau-primary/15 bg-white/95 backdrop-blur z-50">
    <div className="mx-auto max-w-4xl flex items-center justify-between px-4 py-3">
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
              onClick={() => (window.location.href = "/profile")}
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
            >
              Профиль
            </button>
            <button
              onClick={() => (window.location.href = "/recommendations")}
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
            >
              Рекомендации
            </button>
            <button
              onClick={onLogout}
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl bg-red-500/90 text-white hover:bg-red-600 transition"
            >
              Выйти
            </button>
          </>
        ) : (
          <>
            <button
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
              onClick={() => (window.location.href = "/login")}
            >
              Войти
            </button>
            <button
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl bg-tau-primary text-white hover:bg-tau-hover transition"
              onClick={() => (window.location.href = "/register")}
            >
              Регистрация
            </button>
          </>
        )}
      </div>
    </div>
  </div>
);
