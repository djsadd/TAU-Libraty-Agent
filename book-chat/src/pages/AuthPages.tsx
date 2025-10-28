import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const LOGO_URL = "/images/logorgb.png";

/* ==========================
 * Общие вспомогательные UI
 * ========================== */
function LogoHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-3">
      <img src={LOGO_URL} alt="LibraryBot" className="h-8 w-8 rounded-lg object-contain" />
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

function TextInput(
  props: React.InputHTMLAttributes<HTMLInputElement> & { error?: string | null }
) {
  const { error, className = "", ...rest } = props;
  return (
    <div>
      <input
        {...rest}
        className={
          "w-full rounded-xl border px-3 py-2 outline-none transition focus:ring-2 focus:ring-tau-primary/30 " +
          (error
            ? "border-red-400 focus:border-red-400"
            : "border-tau-primary/15 focus:border-tau-primary/40") +
          (className ? ` ${className}` : "")
        }
      />
      {error ? <p className="mt-1 text-xs text-red-500">{error}</p> : null}
    </div>
  );
}

function PasswordInput(
  props: React.InputHTMLAttributes<HTMLInputElement> & { error?: string | null }
) {
  const { error, className = "", ...rest } = props;
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        {...rest}
        type={show ? "text" : "password"}
        className={
          "w-full rounded-xl border px-3 py-2 pr-10 outline-none transition focus:ring-2 focus:ring-tau-primary/30 " +
          (error
            ? "border-red-400 focus:border-red-400"
            : "border-tau-primary/15 focus:border-tau-primary/40") +
          (className ? ` ${className}` : "")
        }
      />
        <button
          type="button"
          onClick={() => setShow(!show)}
          className="absolute inset-y-0 right-2 my-auto h-9 w-9 grid place-items-center rounded-lg text-gray-500 hover:bg-gray-100"
          aria-label={show ? "Скрыть пароль" : "Показать пароль"}
        >
          {show ? (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" width="18" height="18">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18M9.88 9.88A3 3 0 0112 9c1.66 0 3 1.34 3 3 0 .53-.14 1.03-.38 1.46M21 12c0 0-3.58 6-9 6S3 12 3 12s3.58-6 9-6c1.17 0 2.27.22 3.27.63" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" width="18" height="18">
              <path strokeLinecap="round" strokeLinejoin="round" d="M1.5 12S5.5 5.5 12 5.5 22.5 12 22.5 12 18.5 18.5 12 18.5 1.5 12 1.5 12Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          )}
        </button>


      {error ? <p className="mt-1 text-xs text-red-500">{error}</p> : null}
    </div>
  );
}

/* ==========================
 * Страница Входа
 * ========================== */
export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Валидация
    if (!email.trim()) return setError("Укажите e‑mail");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return setError("Некорректный e‑mail");
    if (password.length < 6) return setError("Минимум 6 символов в пароле");

    try {
      setLoading(true);
      // Подключите свой API: /api/auth/login
      const form = new URLSearchParams();
        form.set("username", email);
        form.set("password", password);
        // не обязательно, но можно:
        // form.set("grant_type", "password");
        // form.set("scope", "");

        const res = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: form.toString(),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data?.detail || data?.message || "Не удалось войти");
        }

        const data = await res.json(); // { access_token, token_type: "bearer" }
        const storage = remember ? localStorage : sessionStorage;
        if (data?.access_token) {
          storage.setItem("token", data.access_token);
          storage.setItem("token_type", data.token_type ?? "Bearer");
        }
        navigate("/app");

    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col">
      {/* Хедер */}
      <div className="fixed top-0 w-full border-b border-tau-primary/15 bg-white/95 backdrop-blur z-50">
        <div className="mx-auto max-w-2xl flex items-center justify-between px-4 py-3">
          <LogoHeader title="TAU — LibraryBot" subtitle="Поиск по библиотеке и умные рекомендации" />
          <div className="flex gap-2">
            <Link
              to="/register"
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
            >
              Регистрация
            </Link>
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 flex items-center justify-center pt-[72px] px-4">
        <div className="w-full max-w-md bg-white border border-tau-primary/15 rounded-2xl shadow-sm p-6">
          <h1 className="text-lg font-semibold text-tau-primary">Войти в аккаунт</h1>
          <p className="text-xs text-gray-600 mt-1">Используйте корпоративный e‑mail, если он у вас есть</p>

          {error && (
            <div className="mt-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{error}</div>
          )}

          <form onSubmit={onSubmit} className="mt-4 space-y-3">
            <div>
              <FieldLabel htmlFor="email">E‑mail</FieldLabel>
              <TextInput
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="name@tau-edu.kz"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <FieldLabel htmlFor="password">Пароль</FieldLabel>
              <PasswordInput
                id="password"
                name="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="inline-flex items-center gap-2 select-none">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-tau-primary focus:ring-tau-primary/30"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                Запомнить меня
              </label>
              <Link to="/forgot" className="text-tau-primary hover:underline">Забыли пароль?</Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 rounded-xl bg-tau-primary text-white px-4 py-2 hover:bg-tau-hover transition disabled:opacity-60"
            >
              {loading ? "Входим…" : "Войти"}
            </button>
          </form>

          {/* Соц. провайдеры — опционально */}

          <p className="mt-4 text-xs text-gray-600">
            Нет аккаунта? {" "}
            <Link to="/register" className="text-tau-primary hover:underline">Зарегистрируйтесь</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

/* ==========================
 * Страница Регистрации
 * ========================== */
export function RegisterPage() {
  const navigate = useNavigate();

  // --- новые состояния под бэкенд-поля ---
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const [educationalProgram, setEducationalProgram] = useState("");
  const [languageOfStudy, setLanguageOfStudy] = useState("ru"); // kk | ru | en
  const [role, setRole] = useState("student");                  // student | teacher | staff | admin
  const [university, setUniversity] = useState("Туран-Астана");
  const [faculty, setFaculty] = useState("");
  const [groupName, setGroupName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function phoneClean(v: string) {
    return v.replace(/[^\d+]/g, "");
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // простая валидация
    if (!fullName.trim()) return setError("Укажите ФИО");
    if (!email.trim()) return setError("Укажите e-mail");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return setError("Некорректный e-mail");
    if (password.length < 6) return setError("Минимум 6 символов в пароле");
    if (password !== confirm) return setError("Пароли не совпадают");
    if (!educationalProgram.trim()) return setError("Укажите образовательную программу");
    if (!university.trim()) return setError("Укажите университет");

    try {
      setLoading(true);

      // payload под твой бэкенд (user_data.*)
      const payload = {
        full_name: fullName,
        email,
        password,
        educational_program: educationalProgram,
        language_of_study: languageOfStudy,
        role,
        university,
        faculty,
        group_name: groupName,
        phone_number: phoneClean(phoneNumber),
      };

      const res = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data?.message || "Не удалось зарегистрироваться");
    }

    // НОВОЕ: если сервер сразу даёт токен — сохраним
    const data = await res.json().catch(() => null);
    if (data?.access_token) {
      localStorage.setItem("token", data.access_token);
    }

    navigate("/app");


    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col">
      {/* Хедер */}
      <div className="fixed top-0 w-full border-b border-tau-primary/15 bg-white/95 backdrop-blur z-50">
        <div className="mx-auto max-w-2xl flex items-center justify-between px-4 py-3">
          <LogoHeader title="TAU — LibraryBot" subtitle="Создайте аккаунт для доступа к сервисам" />
          <div className="flex gap-2">
            <Link
              to="/api/login"
              className="text-xs sm:text-sm px-3 py-1.5 rounded-xl border border-tau-primary/20 text-tau-primary hover:bg-tau-primary/10 transition"
            >
              Войти
            </Link>
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 flex items-center justify-center pt-[72px] px-4">
        <div className="w-full max-w-md bg-white border border-tau-primary/15 rounded-2xl shadow-sm p-6">
          <h1 className="text-lg font-semibold text-tau-primary">Регистрация</h1>
          <p className="text-xs text-gray-600 mt-1">Доступ к поиску, рекомендациям и сохранённым запросам</p>

          {error && (
            <div className="mt-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{error}</div>
          )}

          <form onSubmit={onSubmit} className="mt-4 space-y-3">
            <div>
              <FieldLabel htmlFor="full_name">ФИО</FieldLabel>
              <TextInput
                id="full_name"
                name="full_name"
                placeholder="Иванов Иван"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            <div>
              <FieldLabel htmlFor="email">E-mail</FieldLabel>
              <TextInput
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="name@tau-edu.kz"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <FieldLabel htmlFor="password">Пароль</FieldLabel>
                <PasswordInput
                  id="password"
                  name="password"
                  placeholder="Минимум 6 символов"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div>
                <FieldLabel htmlFor="confirm">Повторите пароль</FieldLabel>
                <PasswordInput
                  id="confirm"
                  name="confirm"
                  placeholder="Ещё раз пароль"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                />
              </div>
            </div>

            <div>
              <FieldLabel htmlFor="educational_program">Образовательная программа</FieldLabel>
              <TextInput
                id="educational_program"
                name="educational_program"
                placeholder="6B061 – Информационные системы"
                value={educationalProgram}
                onChange={(e) => setEducationalProgram(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <FieldLabel htmlFor="language_of_study">Язык обучения</FieldLabel>
                <select
                  id="language_of_study"
                  className="w-full rounded-xl border border-tau-primary/15 px-3 py-2 outline-none focus:ring-2 focus:ring-tau-primary/30"
                  value={languageOfStudy}
                  onChange={(e) => setLanguageOfStudy(e.target.value)}
                >
                  <option value="kk">Қазақ</option>
                  <option value="ru">Русский</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div>
                <FieldLabel htmlFor="role">Роль</FieldLabel>
                <select
                  id="role"
                  className="w-full rounded-xl border border-tau-primary/15 px-3 py-2 outline-none focus:ring-2 focus:ring-tau-primary/30"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="student">Студент</option>
                  <option value="teacher">Преподаватель</option>
                  <option value="staff">Сотрудник</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>
            </div>

            <div>
              <FieldLabel htmlFor="university">Университет</FieldLabel>
              <TextInput
                id="university"
                name="university"
                placeholder='Университет "Туран-Астана"'
                value={university}
                onChange={(e) => setUniversity(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <FieldLabel htmlFor="faculty">Факультет</FieldLabel>
                <TextInput
                  id="faculty"
                  name="faculty"
                  placeholder="Факультет ИТ"
                  value={faculty}
                  onChange={(e) => setFaculty(e.target.value)}
                />
              </div>
              <div>
                <FieldLabel htmlFor="group_name">Группа</FieldLabel>
                <TextInput
                  id="group_name"
                  name="group_name"
                  placeholder="IS-23-1"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                />
              </div>
            </div>

            <div>
              <FieldLabel htmlFor="phone_number">Телефон</FieldLabel>
              <TextInput
                id="phone_number"
                name="phone_number"
                placeholder="+7 701 000 00 00"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-1 rounded-xl bg-tau-primary text-white px-4 py-2 hover:bg-tau-hover transition disabled:opacity-60"
            >
              {loading ? "Создаём…" : "Создать аккаунт"}
            </button>
          </form>

          <p className="mt-4 text-xs text-gray-600">
            Уже есть аккаунт?{" "}
            <Link to="/login" className="text-tau-primary hover:underline">Войдите</Link>
          </p>
        </div>
      </div>
    </div>
  );
}


/* ==========================
 * Подсказки по интеграции (прочитайте в чате)
 * ========================== */
export default function _Note() {
  return null;
}
