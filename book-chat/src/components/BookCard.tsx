import React from "react";
import type { Card } from "../utils/aiClient";

interface BookCardProps {
  book: Card;
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

        {book.source === "book_search" && (
          <>
            {book.author && <p className="text-gray-600 text-xs">{book.author}</p>}
            {book.pub_info && <p className="text-gray-500 text-xs">{book.pub_info}</p>}
            {book.year && <p className="text-gray-500 text-xs">{book.year}</p>}
            {book.year && <p className="text-gray-500 text-xs">{book.lang}</p>}
          </>
        )}

        {book.text_snippet && (
          <p className="text-gray-700 text-xs mt-1 line-clamp-3">
            {book.text_snippet}
          </p>
        )}

        {isVector && book.summary && (
          <p className="text-[11px] text-purple-700 mt-2 italic">
            💡 {book.summary}
          </p>
        )}

        <div className="text-[10px] text-gray-400 mt-1 uppercase tracking-wide">
          {isVector ? "Векторный поиск" : "База книг"}
        </div>
      </div>
    </div>
  );
};
