// src/components/BookModal.tsx
import React from "react";
import type { Card } from "../utils/aiClient";

interface BookModalProps {
  book: Card;
  onClose: () => void;
}

export const BookModal: React.FC<BookModalProps> = ({ book, onClose }) => (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="bg-white rounded-2xl p-6 max-w-lg shadow-lg relative overflow-y-auto max-h-[90vh]">
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-gray-500 hover:text-gray-800"
      >
        ✕
      </button>

      {/* Картинка (если есть) */}
      {"cover" in book && book.cover && (
        <img
          src={book.cover}
          alt={book.title}
          className="w-full h-56 object-cover rounded-xl mb-4"
        />
      )}

      <h2 className="text-2xl font-bold mb-1">{book.title}</h2>

      {/* --- Разделяем логику по типу источника --- */}
      {book.source === "book_search" && (
        <>
          <p className="text-gray-600 text-sm mb-2">{book.author}</p>
          {book.pub_info && <p className="text-gray-600 text-sm mb-2">{book.pub_info}</p>}
          {book.subjects && <p className="text-gray-600 text-sm mb-2">{book.subjects}</p>}
          {book.year && <p className="text-gray-600 text-sm mb-2">Год: {book.year}</p>}
          {book.lang && <p className="text-gray-600 text-sm mb-2">Язык: {book.lang}</p>}
        </>
      )}

      {book.source === "vector_search" && (
        <p className="text-gray-500 text-sm mb-3">
          Источник: результат поиска по контексту
        </p>
      )}

      {book.summary && (
        <div className="text-gray-800 text-sm mb-4 leading-relaxed">
          {book.summary}
        </div>
      )}

      {book.text_snippet && (
        <blockquote className="italic text-gray-600 border-l-4 border-blue-400 pl-3 mb-4">
          {book.text_snippet}
        </blockquote>
      )}

      <div className="text-right mt-5">
        <button
          onClick={onClose}
          className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700"
        >
          Закрыть
        </button>
      </div>
    </div>
  </div>
);
