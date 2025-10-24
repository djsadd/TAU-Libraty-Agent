import React from "react";
import type { Book } from "../utils/aiClient";

interface BookCardProps {
  book: Book;
  onClick?: () => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onClick }) => {
  const isVector = book.source === "vector_search";

  return (
    <div
      onClick={onClick}
      className={`bg-white border rounded-lg p-3 cursor-pointer hover:shadow-md transition w-72 ${
        isVector ? "border-purple-300" : "border-blue-300"
      }`}
    >
      <div className="mt-1 text-sm">
        <p className="font-semibold text-gray-800 line-clamp-2">{book.title}</p>
        {book.author && <p className="text-gray-600 text-xs">{book.author}</p>}
        {book.pub_info && <p className="text-gray-500 text-xs">{book.pub_info}</p>}
        {book.year && <p className="text-gray-500 text-xs">{book.year}</p>}

        {/* краткое описание или фрагмент */}
        {book.text_snippet && (
          <p className="text-gray-700 text-xs mt-1 line-clamp-3">
            {book.text_snippet}
          </p>
        )}

        {/* если это карточка из векторного поиска — добавляем summary */}
        {book.summary && isVector && (
          <p className="text-[11px] text-purple-700 mt-2 italic">
            💡 {book.summary}
          </p>
        )}

        {/* метка источника */}
        <div className="text-[10px] text-gray-400 mt-1 uppercase tracking-wide">
          {isVector ? "Векторный поиск" : "База книг"}
        </div>
      </div>
    </div>
  );
};
