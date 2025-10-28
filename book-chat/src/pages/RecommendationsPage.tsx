import React, { useEffect, useState } from "react";
import { fetchAIResponse } from "../utils/aiClient";

const LOGO_URL = "/images/logorgb.png";

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
  download_url?: string | null;
  page?: string | null;
}

/* ===============================
 * Карточки
 * =============================== */
const BookCard: React.FC<{ book: Book }> = ({ book }) => (
  <div className="border border-tau-primary/15 rounded-xl p-3 bg-white hover:bg-tau-primary/5 transition cursor-pointer">
    {book.cover && (
      <img
        src={book.cover}
        alt={book.title}
        className="w-full h-40 object-cover rounded-lg mb-2"
      />
    )}
    <div className="text-sm font-semibold text-tau-primary line-clamp-2">{book.title}</div>
    {book.author && <div className="text-xs text-gray-600">{book.author}</div>}
    {book.year && <div className="text-xs text-gray-400">{book.year}</div>}
    {book.subjects && (
      <div className="text-xs text-gray-500 line-clamp-2 mt-1">{book.subjects}</div>
    )}

    {book.download_url && (
      <a
        href={book.download_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block mt-2 text-xs text-tau-primary hover:underline"
      >
        Читать онлайн →
      </a>
    )}
  </div>
);

const VectorCard: React.FC<{ book: Book }> = ({ book }) => (
  <div className="border border-tau-primary/15 rounded-xl p-3 bg-gray-50 hover:bg-tau-primary/5 transition cursor-pointer">
    <div className="text-sm font-semibold text-tau-primary line-clamp-2">{book.title}</div>
    {book.page && <div className="text-xs text-gray-600 mt-0.5">Стр. {book.page}</div>}
    {book.text_snippet && (
      <div className="text-xs text-gray-500 line-clamp-3 mt-1">{book.text_snippet}</div>
    )}
    {book.download_url && (
      <a
        href={book.download_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block mt-2 text-xs text-tau-primary hover:underline"
      >
        Читать онлайн →
      </a>
    )}
  </div>
);

/* ===============================
 * Основной компонент
 * =============================== */
const RecommendationsPage: React.FC = () => {
  const [vectorBooks, setVectorBooks] = useState<Book[]>([]);
  const [bookResults, setBookResults] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRecommendations() {
      setLoading(true);
      const res = await fetchAIResponse("Философия"); // ← временно фиксированный запрос
      setVectorBooks(res.vector_search || []);
      setBookResults(res.book_search || []);
      setLoading(false);
    }

    loadRecommendations();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Хедер */}
      <div className="sticky top-0 bg-white border-b border-tau-primary/15 z-10 shadow-sm">
        <div className="max-w-4xl mx-auto flex items-center gap-3 px-4 py-3">
          <img src={LOGO_URL} alt="TAU Library" className="h-8 w-8 rounded-lg object-contain" />
          <h1 className="text-lg font-semibold text-tau-primary">Рекомендации книг</h1>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-10">
        {loading ? (
          <div className="text-center text-gray-500 mt-10">Загрузка рекомендаций...</div>
        ) : (
          <>
            {/* Векторные */}
            {vectorBooks.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-tau-primary mb-3">
                  Векторные рекомендации
                </h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {vectorBooks.slice(0, 12).map((book, i) => (
                    <VectorCard key={i} book={book} />
                  ))}
                </div>
              </section>
            )}

            {/* Обзорные */}
            {bookResults.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-tau-primary mb-3">
                  Обзорные рекомендации
                </h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {bookResults.slice(0, 12).map((book, i) => (
                    <BookCard key={i} book={book} />
                  ))}
                </div>
              </section>
            )}

            {bookResults.length === 0 && vectorBooks.length === 0 && (
              <div className="text-center text-gray-500 mt-10">
                Нет доступных рекомендаций.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default RecommendationsPage;
