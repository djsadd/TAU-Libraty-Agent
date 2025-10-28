import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

/* ========== утилиты токена ========== */
function getStoredToken() {
  const ls = localStorage.getItem("token");
  const ss = sessionStorage.getItem("token");
  const type =
    localStorage.getItem("token_type") ||
    sessionStorage.getItem("token_type") ||
    "Bearer";
  return { token: ls || ss || "", type };
}

/* ========== типы данных ========== */
type Lang = "kk" | "ru" | "en";
type Role = "student" | "teacher" | "staff" | "admin";

interface Profile {
  full_name: string;
  email: string;
  educational_program?: string;
  language_of_study?: Lang;
  role: Role;
  university?: string;
  faculty?: string;
  group_name?: string;
  phone_number?: string;
  avatar_url?: string | null;
}

/* --- Мини-компоненты UI (локально, чтобы всё было самодостаточно) --- */
const LOGO_URL = "/images/logorgb.png";

function LogoHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-3">
      {/* Можно заменить на <AcademicCapIcon /> вместо картинки */}
      <img src={LOGO_URL} alt="TAU Library" className="h-8 w-8 rounded-lg object-contain" />
      <div className="flex flex-col leading-tight">
        <span className="text-sm font-semibold text-tau-primary">{title}</span>
        {subtitle && <span className="text-xs text-gray-600">{subtitle}</span>}
      </div>
    </div>
  );
}

function FieldLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="block text-xs font-medium text-gray-600 mb-1">
      {children}
    </label>
  );
}

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & { id: string };

function TextInput({ id, className = "", ...rest }: InputProps) {
  return (
    <input
      id={id}
      className={
        "w-full rounded-xl border border-tau-primary/15 px-3 py-2 outline-none focus:ring-2 focus:ring-tau-primary/30 " +
        className
      }
      {...rest}
    />
  );
}

function PasswordInput({ id, className = "", ...rest }: InputProps) {
  return <TextInput id={id} type="password" className={className} {...rest} />;
}

// УДАЛИ полностью этот блок из profile.tsx




/* ======================================
 *  Страница Профиля
 * ====================================== */
export function ProfilePage() {
  const navigate = useNavigate();

  const [{ token, type }, setAuth] = useState(getStoredToken());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pwdSaving, setPwdSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const [profile, setProfile] = useState<Profile>({
    full_name: "",
    email: "",
    role: "student",
    educational_program: "",
    language_of_study: "ru",
    university: "Туран-Астана",
    faculty: "",
    group_name: "",
    phone_number: "",
    avatar_url: null,
  });

  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const avatarPreview = useMemo(() => {
    if (avatarFile) return URL.createObjectURL(avatarFile);
    return profile.avatar_url || "";
  }, [avatarFile, profile.avatar_url]);

  const [pwd, setPwd] = useState({
    current_password: "",
    new_password: "",
    confirm: "",
  });

  // загрузка профиля
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const { token, type } = getStoredToken();
        if (!token) {
          navigate("/login");
          return;
        }
        setAuth({ token, type });

        const res = await fetch("/auth/me", {
          headers: { Authorization: `${type} ${token}` },
        });
        if (!res.ok) {
          throw new Error("Не удалось загрузить профиль");
        }
        const data = await res.json();
        if (!cancelled) {
          setProfile((p) => ({
            ...p,
            full_name: data.full_name ?? p.full_name,
            email: data.email ?? p.email,
            role: (data.role as Role) ?? p.role,
            educational_program: data.educational_program ?? p.educational_program,
            language_of_study: (data.language_of_study as Lang) ?? p.language_of_study,
            university: data.university ?? p.university,
            faculty: data.faculty ?? p.faculty,
            group_name: data.group_name ?? p.group_name,
            phone_number: data.phone_number ?? p.phone_number,
            avatar_url: data.avatar_url ?? p.avatar_url,
          }));
        }
      } catch (e: any) {
        setError(e.message || "Ошибка загрузки");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(null);

    try {
      setSaving(true);

      // 1) если выбран новый аватар — загрузим
      let avatar_url = profile.avatar_url;
      if (avatarFile) {
        const fd = new FormData();
        fd.append("file", avatarFile);
        const r = await fetch("/auth/avatar", {
          method: "POST",
          headers: { Authorization: `${type} ${token}` },
          body: fd,
        });
        if (!r.ok) {
          const dt = await r.json().catch(() => ({}));
          throw new Error(dt?.message || "Не удалось загрузить аватар");
        }
        const dt = await r.json();
        avatar_url = dt.url || dt.avatar_url || avatar_url;
      }

      // 2) обновим профиль
      const payload = {
        full_name: profile.full_name,
        educational_program: profile.educational_program,
        language_of_study: profile.language_of_study,
        university: profile.university,
        faculty: profile.faculty,
        group_name: profile.group_name,
        phone_number: profile.phone_number?.replace(/[^\d+]/g, ""),
        avatar_url,
      };

      const res = await fetch("/auth/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${type} ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.message || "Не удалось сохранить профиль");
      }

      setProfile((p) => ({ ...p, avatar_url }));
      setOk("Профиль обновлён");
      setAvatarFile(null);
    } catch (e: any) {
      setError(e.message || "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }

  async function savePassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(null);

    if (!pwd.current_password) return setError("Введите текущий пароль");
    if (pwd.new_password.length < 6) return setError("Новый пароль: минимум 6 символов");
    if (pwd.new_password !== pwd.confirm) return setError("Пароли не совпадают");

    try {
      setPwdSaving(true);
      const res = await fetch("/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `${type} ${token}`,
        },
        body: JSON.stringify({
          current_password: pwd.current_password,
          new_password: pwd.new_password,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.message || "Не удалось сменить пароль");
      }
      setOk("Пароль изменён");
      setPwd({ current_password: "", new_password: "", confirm: "" });
    } catch (e: any) {
      setError(e.message || "Ошибка смены пароля");
    } finally {
      setPwdSaving(false);
    }
  }

  function onLogout() {
    try {
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      localStorage.removeItem("token_type");
      sessionStorage.removeItem("token_type");
    } finally {
      navigate("/login");
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col">
      {/* Хедер */}
      <div className="fixed top-0 w-full border-b border-tau-primary/15 bg-white/95 backdrop-blur z-50">
        <div className="mx-auto max-w-3xl flex items-center justify-between px-4 py-3">
          <LogoHeader title="TAU — LibraryBot" subtitle="Профиль пользователя" />
          <div className="flex gap-2">
            <Link
              to="/app"
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
            >
              В приложение
            </Link>
            <Link
              to="/recommendations"
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
            >
              Рекомендации
            </Link>
            <button
              onClick={onLogout}
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-red-300 text-red-600 hover:bg-red-50 transition"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 flex items-start justify-center pt-[72px] px-4 overflow-y-auto">
        <div className="w-full max-w-3xl grid gap-4">
          {/* уведомления */}
          {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{error}</div>}
          {ok && <div className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg p-2">{ok}</div>}

          {/* карточка профиля */}
          <div className="bg-white border border-tau-primary/15 rounded-2xl shadow-sm p-6">
            <h2 className="text-base font-semibold text-tau-primary">Мой профиль</h2>
            <p className="text-xs text-gray-600 mt-1">Основные данные аккаунта</p>

            {loading ? (
              <div className="mt-4 animate-pulse space-y-3">
                <div className="h-6 w-40 bg-gray-100 rounded" />
                <div className="h-9 w-full bg-gray-100 rounded" />
                <div className="h-9 w-full bg-gray-100 rounded" />
                <div className="h-9 w-full bg-gray-100 rounded" />
              </div>
            ) : (
              <form onSubmit={saveProfile} className="mt-4 space-y-4">
                {/* аватар + ФИО + почта */}
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex items-start gap-4">
                    <div className="relative">
                      <div className="h-16 w-16 rounded-xl overflow-hidden bg-gray-100 border border-tau-primary/15">
                        {avatarPreview ? (
                          <img src={avatarPreview} alt="avatar" className="h-full w-full object-cover" />
                        ) : (
                          <div className="h-full w-full grid place-items-center text-gray-400 text-xs">no avatar</div>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2">
                      <label className="text-xs font-medium text-gray-600">Аватар</label>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setAvatarFile(e.target.files?.[0] ?? null)
                        }
                        className="block text-xs file:mr-3 file:rounded-lg file:border file:border-tau-primary/20 file:bg-white file:px-3 file:py-1.5 file:text-xs hover:file:bg-gray-50"
                      />
                      {avatarFile && (
                        <button
                          type="button"
                          onClick={() => setAvatarFile(null)}
                          className="self-start text-[11px] text-gray-600 underline"
                        >
                          Отменить выбор
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1">
                    <div>
                      <FieldLabel htmlFor="full_name">ФИО</FieldLabel>
                      <TextInput
                        id="full_name"
                        value={profile.full_name}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setProfile((p) => ({ ...p, full_name: e.target.value }))
                        }
                      />
                    </div>
                    <div>
                      <FieldLabel htmlFor="email">E-mail</FieldLabel>
                      <TextInput id="email" value={profile.email} className="bg-gray-50" readOnly />
                    </div>
                  </div>
                </div>

                {/* академические поля */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <FieldLabel htmlFor="educational_program">Образовательная программа</FieldLabel>
                    <TextInput
                      id="educational_program"
                      placeholder="6B061 – Информационные системы"
                      value={profile.educational_program || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setProfile((p) => ({ ...p, educational_program: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel htmlFor="language_of_study">Язык обучения</FieldLabel>
                    <select
                      id="language_of_study"
                      className="w-full rounded-xl border border-tau-primary/15 px-3 py-2 outline-none focus:ring-2 focus:ring-tau-primary/30"
                      value={profile.language_of_study || "ru"}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                        setProfile((p) => ({ ...p, language_of_study: e.target.value as Lang }))
                      }
                    >
                      <option value="kk">Қазақ</option>
                      <option value="ru">Русский</option>
                      <option value="en">English</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <FieldLabel htmlFor="university">Университет</FieldLabel>
                    <TextInput
                      id="university"
                      value={profile.university || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setProfile((p) => ({ ...p, university: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel htmlFor="faculty">Факультет</FieldLabel>
                    <TextInput
                      id="faculty"
                      value={profile.faculty || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setProfile((p) => ({ ...p, faculty: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel htmlFor="group_name">Группа</FieldLabel>
                    <TextInput
                      id="group_name"
                      value={profile.group_name || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setProfile((p) => ({ ...p, group_name: e.target.value }))
                      }
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <FieldLabel htmlFor="phone_number">Телефон</FieldLabel>
                    <TextInput
                      id="phone_number"
                      placeholder="+7 701 000 00 00"
                      value={profile.phone_number || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setProfile((p) => ({ ...p, phone_number: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel htmlFor="role">Роль</FieldLabel>
                    <TextInput id="role" value={profile.role} className="bg-gray-50" readOnly />
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={saving}
                    className="rounded-xl bg-tau-primary text-white px-4 py-2 hover:bg-tau-hover transition disabled:opacity-60"
                  >
                    {saving ? "Сохраняем…" : "Сохранить"}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* смена пароля */}
          <div className="bg-white border border-tau-primary/15 rounded-2xl shadow-sm p-6">
            <h2 className="text-base font-semibold text-tau-primary">Смена пароля</h2>
            <p className="text-xs text-gray-600 mt-1">Задайте новый пароль для входа</p>

            <form onSubmit={savePassword} className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <FieldLabel htmlFor="current_password">Текущий пароль</FieldLabel>
                <PasswordInput
                  id="current_password"
                  value={pwd.current_password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setPwd((p) => ({ ...p, current_password: e.target.value }))
                  }
                />
              </div>
              <div>
                <FieldLabel htmlFor="new_password">Новый пароль</FieldLabel>
                <PasswordInput
                  id="new_password"
                  value={pwd.new_password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setPwd((p) => ({ ...p, new_password: e.target.value }))
                  }
                />
              </div>
              <div>
                <FieldLabel htmlFor="confirm_password">Повторите пароль</FieldLabel>
                <PasswordInput
                  id="confirm_password"
                  value={pwd.confirm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setPwd((p) => ({ ...p, confirm: e.target.value }))
                  }
                />
              </div>

              <div className="sm:col-span-3 flex justify-end">
                <button
                  type="submit"
                  disabled={pwdSaving}
                  className="rounded-xl bg-tau-primary text-white px-4 py-2 hover:bg-tau-hover transition disabled:opacity-60"
                >
                  {pwdSaving ? "Обновляем…" : "Обновить пароль"}
                </button>
              </div>
            </form>
          </div>

          {/* опасная зона (опционально) */}
          {/*
          <div className="bg-white border border-red-200 rounded-2xl shadow-sm p-6">
            <h3 className="text-base font-semibold text-red-600">Опасная зона</h3>
            <p className="text-xs text-gray-600 mt-1">Безвозвратные действия</p>
            <button className="mt-3 rounded-xl border border-red-300 text-red-600 px-4 py-2 hover:bg-red-50">
              Удалить аккаунт
            </button>
          </div>
          */}
        </div>
      </div>
    </div>
  );
}
