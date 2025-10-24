import React, { useState } from "react";
import DOMPurify from "dompurify";
import { fetchAIResponse } from "../utils/aiClient";

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

// --- Карточка книги из базы ---
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
      >
        ✕
      </button>

      <h2 className="text-xl font-semibold mb-2">{book.title}</h2>
      {book.author && <p className="text-sm text-gray-600">{book.author}</p>}
      {book.year && <p className="text-sm text-gray-600">{book.year}</p>}
      {book.subjects && (
        <p className="text-sm text-gray-600 mb-2">{book.subjects}</p>
      )}
      {book.text_snippet && (
        <p className="text-sm text-gray-800 mt-3">{book.text_snippet}</p>
      )}
      {book.summary && (
        <p className="text-sm text-gray-700 mt-2">{book.summary}</p>
      )}

      {aiComment && (
        <div className="mt-4 p-3 bg-gray-50 border rounded-lg text-sm text-gray-700">
          <div
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(aiComment.replace(/\n/g, "<br>")),
            }}
          />
        </div>
      )}
    </div>
  </div>
);

// --- Основной компонент чата ---
export const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isTyping, setIsTyping] = useState(false);

// --- Показ первых 6 карточек, потом по 6 добавляем ---
const [visibleBookCount, setVisibleBookCount] = useState(6);
const [visibleVectorCount, setVisibleVectorCount] = useState(6);

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
      // сбрасываем видимость при новом ответе
      setVisibleBookCount(9);
      setVisibleVectorCount(9);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTyping(false);
    }
  }

  return (
    <div className="flex flex-col items-center w-full h-screen bg-gray-50">
      <div className="w-full max-w-2xl flex flex-col h-full border-x bg-white shadow-sm">
        {/* История чата */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
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
        </div>

        {/* Поле ввода */}
        <form
          onSubmit={sendMessage}
          className="border-t p-3 flex gap-2 bg-gray-50"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Введите запрос к ИИ..."
            className="flex-1 border rounded-xl px-3 py-2 focus:outline-none"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-xl"
          >
            Отправить
          </button>
        </form>
      </div>

      {/* Модальное окно книги */}
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
