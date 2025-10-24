import React from "react";
import type { Book } from "../utils/aiClient";

interface BookCardProps {
  book: Book;
  onClick: () => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onClick }) => (
  <div
    onClick={onClick}
    className="bg-white border rounded-lg p-2 cursor-pointer hover:shadow-md transition w-32 sm:w-36"
  >
    {/* <img
      src={book.cover || "https://via.placeholder.com/120x160?text=No+Cover"}
      alt={book.title}
      className="w-full h-40 object-cover rounded-md"
    /> */}

    <div className="mt-1 text-xs text-center">
      <p className="font-semibold truncate">{book.title}</p>
      <p className="text-gray-500 truncate">{book.author}</p>
      <p className="text-gray-500 truncate">{book.pub_info}</p>

      {/* краткое описание */}
      {book.source && (
        <p className="text-gray-600 text-[10px] mt-1 line-clamp-2 overflow-hidden">
          {book.source}
        </p>
      )}
    </div>
  </div>
);