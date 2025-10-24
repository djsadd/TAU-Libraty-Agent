import React from "react";
import type { VectorCard as VectorCardType } from "../utils/aiClient";

interface VectorCardProps {
  book: VectorCardType;
  onClick?: () => void;
}

export const VectorCard: React.FC<VectorCardProps> = ({ book, onClick }) => (
  <div
    onClick={onClick}
    className="bg-white border border-purple-300 rounded-lg p-3 cursor-pointer hover:shadow-md transition w-64"
  >
    <div className="text-sm">
      <p className="font-semibold text-gray-800 line-clamp-2">{book.title}</p>

      {book.text_snippet && (
        <p className="text-gray-700 text-xs mt-1 line-clamp-3">
          {book.text_snippet}
        </p>
      )}

      {book.summary && (
        <p className="text-[11px] text-purple-700 mt-2 italic">
          💡 {book.summary}
        </p>
      )}
    </div>

    <div className="text-[10px] text-purple-500 mt-1 uppercase tracking-wide">
      🔍 Векторный поиск
    </div>
  </div>
);
