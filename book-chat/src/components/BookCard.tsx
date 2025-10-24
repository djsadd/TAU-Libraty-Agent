import React, { useState } from "react";
import { BookCard } from "./BookCard";
import type { Card } from "../utils/aiClient";

interface BookListProps {
  books: Card[];
  onCardClick?: (book: Card) => void;
}

export const BookList: React.FC<BookListProps> = ({ books, onCardClick }) => {
  const [visibleCount, setVisibleCount] = useState(3);

  const handleLoadMore = () => {
    setVisibleCount((prev) => prev + 3); // Показывать по 3 карточки за раз
  };

  const visibleBooks = books.slice(0, visibleCount);

  return (
    <div className="flex flex-col items-center">
      <div className="flex flex-wrap justify-center gap-4">
        {visibleBooks.map((book, index) => (
          <BookCard key={index} book={book} onClick={() => onCardClick?.(book)} />
        ))}
      </div>

      {visibleCount < books.length && (
        <button
          onClick={handleLoadMore}
          className="mt-4 px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
        >
          Загрузить ещё
        </button>
      )}
    </div>
  );
};
