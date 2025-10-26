import React, { useEffect, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { fetchAIResponse } from "../utils/aiClient";

const LOGO_URL = "/images/logorgb.png";

// --- Типы ---
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

// --- Карточка книги ---
const BookCard: React.FC<{ book: Book; onClick: () => void }> = ({
  book,
  onClick,
}) => (
  <div
    onClick={onClick}
    className="border rounded-xl p-2 cursor-pointer bg-white hover:bg-blue-50 transition"
  >
    <div className="text-sm font-semibold truncate">{book.title}</div>
    {book.author && (
      <div className="text-xs text-gray-500 truncate">{book.author}</div>
    )}
    {book.year && <div className="text-xs text-gray-400">{book.year}</div>}
    {book.subjects && (
      <div className="text-xs text-gray-400 truncate">{book.subjects}</div>
    )}
  </div>
);

// --- Карточка из векторного поиска ---
const VectorCard: React.FC<{ book: Book; onClick: () => void }> = ({
  book,
  onClick,
}) => (
  <div
    onClick={onClick}
    className="border rounded-xl p-2 cursor-pointer bg-gray-50 hover:bg-blue-50 transition"
  >
    <div className="text-sm font-semibold truncate">{book.title}</div>
    {book.page && <div className="text-xs text-gray-500">Стр. {book.page}</div>}
    {book.text_snippet && (
      <div className="text-xs text-gray-400 line-clamp-2">
        {book.text_snippet}
      </div>
    )}
  </div>
);

// --- Модалка книги ---
const BookModal: React.FC<{
  book: Book;
  aiComment?: string;
  onClose: () => void;
}> = ({ book, aiComment, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl relative">
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-gray-500 hover:text-gray-800"
        aria-label="Закрыть"
      >
        ✕
      </button>

      <h2 className="text-xl font-semibold mb-2">{book.title}</h2>
      {book.author && <p className="text-sm text-gray-600">{book.author}</p>}
      {book.year && <p className="text-sm text-gray-600">{book.year}</p>}
      {book.subjects && (
        <p className="text-sm text-gray-600 mb-2">{book.subjects}</p>
      )}

      {aiComment && book.summary && (
        <div className="mt-4 p-3 bg-gray-50 border rounded-lg text-sm text-gray-700">
          <div
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(book.summary.replace(/\n/g, "<br>")),
            }}
          />
        </div>
      )}
    </div>
  </div>
);

// --- Фиксированный хедер ---
const HeaderBar: React.FC = () => (
  <div className="fixed top-0 w-full border-b bg-white z-50">
    <div className="mx-auto max-w-2xl flex items-center gap-3 px-4 py-3">
      <img
        src={LOGO_URL}
        alt="TAU Library"
        className="h-8 w-8 rounded-lg object-contain"
      />
      <div className="flex flex-col leading-tight">
        <span className="text-sm font-semibold text-gray-900">
          TAU — Library Assistant
        </span>
        <span className="text-xs text-gray-500">
          Поиск по библиотеке и умные рекомендации
        </span>
      </div>
    </div>
  </div>
);

// --- Приветственный блок ---
const IntroCard: React.FC = () => (
  <div className="px-4 pt-4">
    <div className="mx-auto max-w-2xl bg-gradient-to-b from-blue-50 to-white border border-blue-100 rounded-2xl shadow-sm p-5">
      <div className="flex items-start gap-3">
        <img
          src={LOGO_URL}
          alt="TAU Library"
          className="h-10 w-10 rounded-xl object-contain"
        />
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Найдите нужную книгу или узнайте о библиотеке
          </h1>
          <ul className="mt-2 text-sm text-gray-700 space-y-1">
            <li>• Поиск книг по названию, автору или теме</li>
            <li>• Информация о библиотеке и её ресурсах</li>
            <li>• Рекомендации на основе ваших интересов</li>
          </ul>
          <p className="mt-3 text-xs text-gray-500">
            Подсказка: попробуйте запрос «сетевые технологии Таненбаум» или
            «книги по управлению проектами».
          </p>
        </div>
      </div>
    </div>
  </div>
);

// --- Основной компонент ---
export const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isTyping, setIsTyping] = useState(false);

  const [visibleBookCount, setVisibleBookCount] = useState(6);
  const [visibleVectorCount, setVisibleVectorCount] = useState(6);

  // --- ключ: ссылочный элемент для автоскролла
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const loadMoreBooks = () => setVisibleBookCount((prev) => prev + 6);
  const loadMoreVectors = () => setVisibleVectorCount((prev) => prev + 6);

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

  // --- автоскролл при изменении сообщений и статуса набора
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isTyping]);

  return (
    <div className="flex flex-col w-full h-screen bg-gray-50 overflow-hidden">
      <HeaderBar />

      {/* Основной блок под хедером */}
      <div className="flex flex-col flex-1 items-center pt-[72px] overflow-hidden min-h-0">
        {messages.length === 0 && <IntroCard />}

        <div className="w-full max-w-2xl flex flex-col flex-1 border-x bg-white shadow-sm min-h-0">
          {/* История чата */}
          <div
            className="flex-1 overflow-y-auto min-h-0 p-3 space-y-4 mb-[56px]"
            style={{ WebkitOverflowScrolling: "touch" }}
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                {msg.text && (
                  <div
                    className={`rounded-2xl px-4 py-2 max-w-xs ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-900"
                    }`}
                  >
                    {msg.text}
                  </div>
                )}

                {msg.reply && (
                  <div
                    className="mt-2 prose prose-sm max-w-none bg-gray-50 border rounded-xl p-3"
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(
                        msg.reply.replace(/\n/g, "<br>")
                      ),
                    }}
                  />
                )}

                {/* Векторные карточки */}
                {msg.vector_search && msg.vector_search.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-xs text-gray-500 mb-1">
                      Релевантные книги (векторный поиск)
                    </h4>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                      {msg.vector_search
                        .slice(0, visibleVectorCount)
                        .map((book, j) => (
                          <VectorCard
                            key={j}
                            book={book}
                            onClick={() => setSelectedBook(book)}
                          />
                        ))}
                    </div>

                    {msg.vector_search.length > visibleVectorCount && (
                      <div className="flex justify-center mt-2">
                        <button
                          onClick={loadMoreVectors}
                          className="text-xs px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
                        >
                          Загрузить ещё
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Базовые карточки */}
                {msg.book_search && msg.book_search.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-xs text-gray-500 mb-1">
                      Найдено в базе книг
                    </h4>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                      {msg.book_search
                        .slice(0, visibleBookCount)
                        .map((book, j) => (
                          <BookCard
                            key={j}
                            book={book}
                            onClick={() => setSelectedBook(book)}
                          />
                        ))}
                    </div>

                    {msg.book_search.length > visibleBookCount && (
                      <div className="flex justify-center mt-2">
                        <button
                          onClick={loadMoreBooks}
                          className="text-xs px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
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
              <div className="flex items-center space-x-2 text-gray-500 text-sm">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                <span>ИИ печатает...</span>
              </div>
            )}

            {/* якорь для скролла */}
            <div ref={messagesEndRef} />
          </div>

          {/* Поле ввода */}
          <form
            onSubmit={sendMessage}
            className="border-t p-3 flex gap-2 bg-gray-50 shrink-0"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Введите запрос к ИИ..."
              className="flex-1 border rounded-xl px-3 py-2 focus:outline-none"
              aria-label="Сообщение"
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded-xl"
            >
              Отправить
            </button>
          </form>
        </div>
      </div>

      {/* Модальное окно */}
      {selectedBook && (
        <BookModal
          book={selectedBook}
          aiComment={messages[messages.length - 1]?.reply}
          onClose={() => setSelectedBook(null)}
        />
      )}
    </div>
  );
};
