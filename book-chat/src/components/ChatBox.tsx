import React, { useState } from "react";
import DOMPurify from "dompurify";
import { fetchAIResponse } from "../utils/aiClient";
import type { Book } from "../utils/aiClient";
import { BookCard } from "./BookCard";
import { BookModal } from "./BookModal";

interface Message {
  role: "user" | "assistant";
  text?: string;
  reply?: string;
  vector_search?: Book[];
  book_search?: Book[];
}

export const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [isTyping, setIsTyping] = useState(false);

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

              {/* Карточки из vector_search */}
              {msg.vector_search && msg.vector_search.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-xs text-gray-500 mb-1">
                    Релевантные книги (векторный поиск)
                  </h4>
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                    {msg.vector_search.map((book, j) => (
                      <BookCard
                        key={j}
                        book={book}
                        onClick={() => setSelectedBook(book)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Карточки из book_search */}
              {msg.book_search && msg.book_search.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-xs text-gray-500 mb-1">
                    Найдено в базе книг
                  </h4>
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                    {msg.book_search.map((book, j) => (
                      <BookCard
                        key={j}
                        book={book}
                        onClick={() => setSelectedBook(book)}
                      />
                    ))}
                  </div>
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
        <form onSubmit={sendMessage} className="border-t p-3 flex gap-2 bg-gray-50">
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
