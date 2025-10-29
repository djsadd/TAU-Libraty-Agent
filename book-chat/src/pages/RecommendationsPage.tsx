import React, { useEffect, useMemo, useState } from "react";
import { HeaderBar } from "../components/HeaderBar";
import { fetchAIResponse } from "../utils/aiClient";

const LOGO_URL = "/images/logorgb.png";

export interface Book {
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

interface TopicResult {
  reply: string;
  book_search?: Book[];
  vector_search?: Book[];
}

type RecommendationsResponse = Record<string, TopicResult>;

function isAuthenticated() {
  return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

const BookCard: React.FC<{ book: Book }> = ({ book }) => (
  <div className="border border-tau-primary/15 rounded-xl p-3 bg-white hover:bg-tau-primary/5 transition">
    {book.cover && (
      <img src={book.cover} alt={book.title} className="w-full h-40 object-cover rounded-lg mb-2" />
    )}
    <div className="text-sm font-semibold text-tau-primary line-clamp-2">{book.title}</div>
    {book.author && <div className="text-xs text-gray-600">{book.author}</div>}
    {book.year && <div className="text-xs text-gray-400">{book.year}</div>}
    {book.subjects && <div className="text-xs text-gray-500 line-clamp-2 mt-1">{book.subjects}</div>}
    {book.download_url && (
      <a href={book.download_url} target="_blank" rel="noopener noreferrer" className="block mt-2 text-xs text-tau-primary hover:underline">Читать онлайн →</a>
    )}
  </div>
);

const VectorCard: React.FC<{ book: Book }> = ({ book }) => (
  <div className="border border-tau-primary/15 rounded-xl p-3 bg-gray-50 hover:bg-tau-primary/5 transition">
    <div className="text-sm font-semibold text-tau-primary line-clamp-2">{book.title}</div>
    {book.page && <div className="text-xs text-gray-600 mt-0.5">Стр. {book.page}</div>}
    {book.text_snippet && <div className="text-xs text-gray-500 line-clamp-3 mt-1">{book.text_snippet}</div>}
    {book.download_url && (
      <a href={book.download_url} target="_blank" rel="noopener noreferrer" className="block mt-2 text-xs text-tau-primary hover:underline">Читать онлайн →</a>
    )}
  </div>
);

const TopicSection: React.FC<{ topic: string; data: TopicResult }> = ({ topic, data }) => {
  const vectorBooks = data.vector_search ?? [];
  const bookResults = data.book_search ?? [];
  const empty = vectorBooks.length === 0 && bookResults.length === 0;

  return (
    <section className="bg-white/60 rounded-2xl p-4 md:p-6 border border-gray-200">
      <div className="flex items-center gap-3 mb-3">
        <img src={LOGO_URL} alt="TAU Library" className="h-7 w-7 rounded-md object-contain" />
        <h2 className="text-lg md:text-xl font-semibold text-tau-primary">{topic}</h2>
      </div>
      {data.reply && <p className="text-sm text-gray-600 mb-4">{data.reply}</p>}
      {!empty ? (
        <div className="space-y-8">
          {vectorBooks.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-tau-primary mb-3">Векторные рекомендации</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {vectorBooks.slice(0, 12).map((book, i) => <VectorCard key={`v-${topic}-${i}`} book={book} />)}
              </div>
            </div>
          )}
          {bookResults.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-tau-primary mb-3">Обзорные рекомендации</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {bookResults.slice(0, 12).map((book, i) => <BookCard key={`b-${topic}-${i}`} book={book} />)}
              </div>
            </div>
          )}
        </div>
      ) : <div className="text-center text-gray-500">Нет карточек по теме.</div>}
    </section>
  );
};

const RecommendationsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RecommendationsResponse>({});

  const [isAuth, setIsAuth] = useState(isAuthenticated());
  const handleLogout = () => {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    setIsAuth(false);
    window.location.href = "/login";
  };

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "token") setIsAuth(isAuthenticated());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const res: unknown = await fetchAIResponse("Рекомендации по темам");
        console.log("Ответ от бэкенда:", res);
        if (res && typeof res === "object" && !Array.isArray(res)) {
          setData(res as RecommendationsResponse);
        } else {
          throw new Error("Неожиданный формат ответа сервера");
        }
      } catch (e: any) {
        console.error("Ошибка при загрузке:", e);
        setError(e?.message || "Ошибка загрузки рекомендаций");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const topics = useMemo(() => Object.keys(data), [data]);
  const totals = useMemo(() => {
    let v = 0; let b = 0;
    for (const t of Object.values(data)) {
      v += t.vector_search?.length || 0;
      b += t.book_search?.length || 0;
    }
    return { v, b, all: v + b };
  }, [data]);

  return (
    <div className="fixed inset-0 flex flex-col w-full bg-gray-50 overflow-auto">
      <HeaderBar isAuth={isAuth} onLogout={handleLogout} />
      <div className="pt-[72px] pb-16">
        <div className="max-w-6xl mx-auto px-4 py-6 space-y-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={LOGO_URL} alt="TAU Library" className="h-8 w-8 rounded-lg object-contain" />
              <div>
                <h1 className="text-lg md:text-xl font-semibold text-tau-primary">Рекомендации по тематикам</h1>
                <p className="text-xs text-gray-500">Всего карточек: {totals.all} · Векторных: {totals.v} · Обзорных: {totals.b}</p>
              </div>
            </div>
          </div>
          {loading && <div className="text-center text-gray-500 mt-10">Загрузка рекомендаций...</div>}
          {error && <div className="text-center text-red-600 mt-6">{error}</div>}
          {!loading && !error && topics.length === 0 && <div className="text-center text-gray-500 mt-10">Нет доступных рекомендаций.</div>}
          {!loading && !error && topics.length > 0 && (
            <div className="space-y-6">
              {topics.map((topic) => (<TopicSection key={topic} topic={topic} data={data[topic]} />))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecommendationsPage;
