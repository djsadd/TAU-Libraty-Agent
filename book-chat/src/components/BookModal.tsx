// src/components/BookModal.tsx
import React from "react";
import type { Book } from "../utils/aiClient";

interface BookModalProps {
  book: Book;
  onClose: () => void;
  aiComment?: string; // ← добавлено для текста LLM
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

      {book.cover && (
        <img
          src={book.cover}
          alt={book.title}
          className="w-full h-56 object-cover rounded-xl mb-4"
        />
      )}

      <h2 className="text-2xl font-bold mb-1">{book.title}</h2>
      <p className="text-gray-600 mb-3 text-sm">{book.author}</p>
      <p className="text-gray-600 mb-3 text-sm">{book.pub_info}</p>
      <p className="text-gray-600 mb-3 text-sm">{book.subjects}</p>
      <p className="text-gray-600 mb-3 text-sm">{book.year}</p>
      <p className="text-gray-600 mb-3 text-sm">{book.lang}</p>

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

      {/* {aiComment && (
        <div className="border-t pt-3 mt-4 text-gray-700 text-sm">
          <h3 className="font-semibold mb-1 text-blue-600">Комментарий ИИ:</h3>
          <div
            className="prose prose-sm"
            dangerouslySetInnerHTML={{
              __html: aiComment.replace(/\n/g, "<br>"),
            }}
          />
        </div>
      )} */}

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
