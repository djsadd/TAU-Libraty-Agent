import React, { useEffect, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { fetchAIResponse } from "../utils/aiClient";

const LOGO_URL = "/images/logorgb.png";

/* ==========================
 * Вспомогательное
 * ========================== */
// простая проверка авторизации: есть ли токен в localStorage / sessionStorage
function isAuthenticated() {
  return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

/* ==========================
 * Типы
 * ========================== */
interface Book {
  title: string;
  author?: string;
  pub_info?: string;
  year?: string;
  subjects?: string;
  lang?: string;
  id_book?: string;
  text_snippet?: string;
  summary?: string;
  cover?: string;
  page?: string | null;
}

interface Message {
  role: "user" | "assistant";
  text?: string;
  reply?: string;
  vector_search?: Book[];
  book_search?: Book[];
}

/* ==========================
 * UI карточки
 * ========================== */
const BookCard: React.FC<{ book: Book; onClick: () => void }> = ({ book, onClick }) => (
  <div
    onClick={onClick}
    className="border border-tau-primary/15 rounded-xl p-2 cursor-pointer bg-white hover:bg-tau-primary/5 transition"
  >
    <div className="text-sm font-semibold text-tau-primary truncate">{book.title}</div>
    {book.author && <div className="text-xs text-gray-500 truncate">{book.author}</div>}
    {book.year && <div className="text-xs text-gray-400">{book.year}</div>}
    {book.subjects && <div className="text-xs text-gray-400 truncate">{book.subjects}</div>}
  </div>
);

const VectorCard: React.FC<{ book: Book; onClick: () => void }> = ({ book, onClick }) => (
  <div
    onClick={onClick}
    className="border border-tau-primary/15 rounded-xl p-2 cursor-pointer bg-gray-50 hover:bg-tau-primary/5 transition"
  >
    <div className="text-sm font-semibold text-tau-primary truncate">{book.title}</div>
    {book.page && <div className="text-xs text-gray-500">Стр. {book.page}</div>}
    {book.text_snippet && <div className="text-xs text-gray-500 line-clamp-2">{book.text_snippet}</div>}
  </div>
);

/* ==========================
 * Модалка книги (умеет показывать стрим)
 * ========================== */
const BookModal: React.FC<{
  book: Book;
  aiComment?: string; // fallback
  streamed?: string;  // текст, который приходит потоково и/или из кэша
  loading?: boolean;  // флажок загрузки
  onClose: () => void;
}> = ({ book, aiComment, streamed, loading, onClose }) => {
  const html = (streamed || book.summary || aiComment || "").replace(/\n/g, "<br>");

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl relative border border-tau-primary/15">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-800"
          aria-label="Закрыть"
        >
          ✕
        </button>

        <h2 className="text-xl font-semibold text-tau-primary mb-1">{book.title}</h2>
        {book.author && <p className="text-sm text-gray-600">{book.author}</p>}
        {book.year && <p className="text-sm text-gray-600">{book.year}</p>}
        {book.subjects && <p className="text-sm text-gray-600 mb-2">{book.subjects}</p>}

        <div className="mt-4 p-3 bg-gray-50 border border-tau-primary/10 rounded-lg text-sm text-gray-700 min-h-[96px]">
          {loading && (
            <div className="flex items-center gap-2 text-tau-primary mb-2">
              <span className="w-2 h-2 rounded-full bg-tau-primary animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-tau-primary animate-bounce delay-100" />
              <span className="w-2 h-2 rounded-full bg-tau-primary animate-bounce delay-200" />
              <span>Генерирую контекст…</span>
            </div>
          )}

          {(streamed || aiComment || book.summary) ? (
            <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
          ) : (
            !loading && <div className="text-gray-500">Нет данных.</div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ==========================
 * Фиксированный хедер
 * ========================== */
const HeaderBar: React.FC<{ isAuth: boolean; onLogout: () => void }> = ({ isAuth, onLogout }) => (
  <div className="fixed top-0 w-full border-b border-tau-primary/15 bg-white/95 backdrop-blur z-50">
    <div className="mx-auto max-w-2xl flex items-center justify-between px-4 py-3">
      {/* Логотип и подпись */}
      <div className="flex items-center gap-3">
        <img src={LOGO_URL} alt="TAU Library" className="h-8 w-8 rounded-lg object-contain" />
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold text-tau-primary">TAU — Library Assistant</span>
          <span className="text-xs text-gray-600">Поиск по библиотеке и умные рекомендации</span>
        </div>
      </div>

      {/* Кнопки справа */}
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

/* ==========================
 * Приветственный блок
 * ========================== */
const IntroCard: React.FC = () => (
  <div className="px-4 pt-4">
    <div className="mx-auto max-w-2xl bg-gradient-to-b from-tau-primary/10 to-white border border-tau-primary/15 rounded-2xl shadow-sm p-5">
      <div className="flex items-start gap-3">
        <img src={LOGO_URL} alt="TAU Library" className="h-10 w-10 rounded-xl object-contain" />
        <div>
          <h1 className="text-lg font-semibold text-tau-primary">Найдите нужную книгу или узнайте о библиотеке</h1>
          <ul className="mt-2 text-sm text-gray-700 space-y-1">
            <li>• Поиск книг по названию, автору или теме</li>
            <li>• Информация о библиотеке и её ресурсах</li>
            <li>• Рекомендации на основе ваших интересов</li>
          </ul>
          <p className="mt-3 text-xs text-gray-500">
            Подсказка: попробуйте запрос «сетевые технологии Таненбаум» или «книги по управлению проектами».
          </p>
        </div>
      </div>
    </div>
  </div>
);

/* ==========================
 * Основной компонент чата
 * ========================== */
export const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isTyping, setIsTyping] = useState(false);

  const [visibleBookCount, setVisibleBookCount] = useState(6);
  const [visibleVectorCount, setVisibleVectorCount] = useState(6);

  const [isAuth, setIsAuth] = useState(isAuthenticated());

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // ======= КЭШ + управление стримом =======
  // Ключ = id_book + page (если нет id — используем title)
  function ctxKey(b: Book) {
    return `${b.id_book || b.title || "no-id"}::${b.page || "n/a"}`;
  }

  const [ctxCache, setCtxCache] = useState<Record<string, string>>({});
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const loadMoreBooks = () => setVisibleBookCount((prev) => prev + 6);
  const loadMoreVectors = () => setVisibleVectorCount((prev) => prev + 6);

  const handleLogout = () => {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    setIsAuth(false);
  };

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetchAIResponse(input);
      const aiMsg: Message = {
        role: "assistant",
        reply: res.reply,
        vector_search: res.vector_search,
        book_search: res.book_search,
      };
      setMessages((prev) => [...prev, aiMsg]);
      setVisibleBookCount(9);
      setVisibleVectorCount(9);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTyping(false);
    }
  }

  // ======= Открытие векторной карточки с ленивым стримом =======
  function openVectorBook(book: Book) {
    setSelectedBook(book);

    const key = ctxKey(book);
    // если уже есть в кэше — просто показываем
    if (ctxCache[key]) return;

    // прерываем предыдущий стрим, если ещё идёт
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    setLoadingKey(key);

    (async () => {
      try {
        // подстрой body под контракт бэкенда
        const resp = await fetch("/api/generate_llm_context", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id_book: book.id_book,
            title: book.title,
            page: book.page,
          }),
          signal: ac.signal,
        });

        if (!resp.ok || !resp.body) throw new Error("Bad response");

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let acc = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          acc += decoder.decode(value, { stream: true });

          // обновляем кэш «по ходу»
          setCtxCache((prev) => ({ ...prev, [key]: acc }));
        }

        // финальный докод
        acc += new TextDecoder().decode();
        setCtxCache((prev) => ({ ...prev, [key]: acc.trim() }));
      } catch (e: any) {
        if (e?.name !== "AbortError") console.error(e);
      } finally {
        setLoadingKey(null);
      }
    })();
  }

  // закрытие модалки — гасим активный стрим
  function closeModal() {
    abortRef.current?.abort();
    setSelectedBook(null);
  }

  // автоскролл
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isTyping]);

  // реагировать на изменения токена в другой вкладке
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "token") setIsAuth(isAuthenticated());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // лёгкий триггер обновить auth-состояние
  useEffect(() => {
    setIsAuth(isAuthenticated());
  }, [messages.length]);

  // на размонтирование компонента — оборвать стрим
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  return (
    <div className="fixed inset-0 flex flex-col w-full bg-gray-50 overflow-hidden">
      <HeaderBar isAuth={isAuth} onLogout={handleLogout} />

      <div className="flex flex-col flex-1 items-center pt-[72px] overflow-hidden min-h-0">
        {messages.length === 0 && <IntroCard />}

        <div className="w-full max-w-2xl flex flex-col flex-1 border-x border-tau-primary/15 bg-white shadow-sm min-h-0">
          <div
            className="flex-1 overflow-y-auto min-h-0 p-3 space-y-4 mb-[56px]"
            style={{ WebkitOverflowScrolling: "touch" }}
          >
            {messages.map((msg, i) => (
              <div key={i} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                {msg.text && (
                  <div
                    className={`rounded-2xl px-4 py-2 max-w-xs ${
                      msg.role === "user" ? "bg-tau-primary text-white" : "bg-gray-100 text-gray-900"
                    }`}
                  >
                    {msg.text}
                  </div>
                )}

                {msg.reply && (
                  <div
                    className="mt-2 prose prose-sm max-w-none bg-gray-50 border border-tau-primary/10 rounded-xl p-3"
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(msg.reply.replace(/\n/g, "<br>")) }}
                  />
                )}

                {msg.vector_search && msg.vector_search.length > 0 && (
                  <div className="mt-3 w-full">
                    <h4 className="text-xs text-gray-500 mb-1">Релевантные книги (векторный поиск)</h4>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                      {msg.vector_search.slice(0, visibleVectorCount).map((book, j) => (
                        <VectorCard key={j} book={book} onClick={() => openVectorBook(book)} />
                      ))}
                    </div>

                    {msg.vector_search.length > visibleVectorCount && (
                      <div className="flex justify-center mt-2">
                        <button
                          className="text-xs px-3 py-1 bg-tau-primary hover:bg-tau-hover text-white rounded-lg transition"
                          onClick={loadMoreVectors}
                        >
                          Загрузить ещё
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {msg.book_search && msg.book_search.length > 0 && (
                  <div className="mt-3 w-full">
                    <h4 className="text-xs text-gray-500 mb-1">Найдено в базе книг</h4>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                      {msg.book_search.slice(0, visibleBookCount).map((book, j) => (
                        <BookCard key={j} book={book} onClick={() => setSelectedBook(book)} />
                      ))}
                    </div>

                    {msg.book_search.length > visibleBookCount && (
                      <div className="flex justify-center mt-2">
                        <button
                          className="text-xs px-3 py-1 bg-tau-primary hover:bg-tau-hover text-white rounded-lg transition"
                          onClick={loadMoreBooks}
                        >
                          Загрузить ещё
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center space-x-2 text-sm text-tau-primary">
                <div className="w-2 h-2 bg-tau-primary rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-tau-primary rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-tau-primary rounded-full animate-bounce delay-200" />
                <span>ИИ печатает...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={sendMessage} className="border-t border-tau-primary/15 p-3 flex gap-2 bg-gray-50 shrink-0">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Введите запрос к ИИ..."
              className="flex-1 border border-tau-primary/15 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-tau-primary/30"
              aria-label="Сообщение"
            />
            <button
              type="submit"
              className="bg-tau-primary hover:bg-tau-hover text-white px-4 py-2 rounded-xl transition"
            >
              Отправить
            </button>
          </form>
        </div>
      </div>

      {selectedBook && (
        <BookModal
          book={selectedBook}
          aiComment={messages[messages.length - 1]?.reply}
          streamed={ctxCache[ctxKey(selectedBook)]}
          loading={loadingKey === ctxKey(selectedBook)}
          onClose={closeModal}
        />
      )}
    </div>
  );
};
