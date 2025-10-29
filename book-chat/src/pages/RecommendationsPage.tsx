// src/pages/RecommendationsPage.tsx
import React, { useEffect, useMemo, useState } from "react";
import { HeaderBar } from "../components/HeaderBar";
import {
  fetchEducationalDisciplineList,
  fetchChatCardsByDiscipline,
  type ChatCardResponse,
  type ChatCardBook,
} from "../utils/eduClient";


const LOGO_URL = "/images/logorgb.png";

/* ==========================
 * Вспомогательное
 * ========================== */
function isAuthenticated() {
  return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

/* ==========================
 * Карточки результатов
 * ========================== */
const BookCard: React.FC<{ book: ChatCardBook }> = ({ book }) => (
  <div className="border border-tau-primary/15 rounded-xl p-3 bg-white hover:bg-tau-primary/5 transition">
    {book.cover && (
      <img src={book.cover} alt={book.title} className="w-full h-40 object-cover rounded-lg mb-2" />
    )}
    <div className="text-sm font-semibold text-tau-primary line-clamp-2">{book.title}</div>
    {book.author && <div className="text-xs text-gray-600">{book.author}</div>}
    {book.year && <div className="text-xs text-gray-400">{book.year}</div>}
    {book.subjects && <div className="text-xs text-gray-500 line-clamp-2 mt-1">{book.subjects}</div>}
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

const VectorCard: React.FC<{ book: ChatCardBook }> = ({ book }) => (
  <div className="border border-tau-primary/15 rounded-xl p-3 bg-gray-50 hover:bg-tau-primary/5 transition">
    <div className="text-sm font-semibold text-tau-primary line-clamp-2">{book.title}</div>
    {book.page && <div className="text-xs text-gray-600 mt-0.5">Стр. {book.page}</div>}
    {book.text_snippet && <div className="text-xs text-gray-500 line-clamp-3 mt-1">{book.text_snippet}</div>}
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

/* ==========================
 * Модалка результатов
 * ========================== */
/* ==========================
 * Модалка результатов (скролл внутри)
 * ========================== */
const ResultsModal: React.FC<{
  open: boolean;
  onClose: () => void;
  discipline: string | null;
  loading: boolean;
  error: string | null;
  data: ChatCardResponse | null;
}> = ({ open, onClose, discipline, loading, error, data }) => {
  // Закрытие по Esc + блокируем скролл фона, пока модалка открыта
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const v = data?.vector_search ?? [];
  const b = data?.book_search ?? [];
  const empty = !loading && !error && v.length === 0 && b.length === 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-label={discipline || "Результаты"}
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* panel: ограничиваем высоту и включаем внутренний скролл */}
      <div className="relative w-full max-w-5xl bg-white rounded-2xl shadow-xl border border-gray-200
                      max-h-[85vh] overflow-y-auto">
        {/* sticky header — всегда виден при прокрутке */}
        <div className="sticky top-0 z-10 bg-white/95 backdrop-blur border-b border-gray-200">
          <div className="flex items-center justify-between px-4 md:px-6 py-3">
            <div className="flex items-center gap-3">
              <img src={LOGO_URL} alt="TAU Library" className="h-7 w-7 rounded-md object-contain" />
              <h2 className="text-lg md:text-xl font-semibold text-tau-primary">
                {discipline || "Результаты"}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs rounded-md border border-gray-300 hover:bg-gray-100"
            >
              Закрыть
            </button>
          </div>
        </div>

        {/* content */}
        <div className="px-4 md:px-6 py-4">
          {loading && <div className="text-center text-gray-500 py-8">Загрузка карточек…</div>}
          {error && <div className="text-center text-red-600 py-4">{error}</div>}

          {!loading && !error && data?.reply && (
            <p className="text-sm text-gray-600 mb-4">{data.reply}</p>
          )}

          {!loading && !error && (
            <>
              {empty && (
                <div className="text-center text-gray-500 py-8">
                  Нет карточек по этой дисциплине.
                </div>
              )}

              {v.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-base font-semibold text-tau-primary mb-3">
                    Векторные рекомендации
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {v.slice(0, 24).map((book, i) => (
                      <VectorCard key={`v-${i}`} book={book} />
                    ))}
                  </div>
                </div>
              )}

              {b.length > 0 && (
                <div>
                  <h3 className="text-base font-semibold text-tau-primary mb-3">
                    Обзорные рекомендации
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {b.slice(0, 24).map((book, i) => (
                      <BookCard key={`b-${i}`} book={book} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};


/* ==========================
 * Страница
 * ========================== */
const RecommendationsPage: React.FC = () => {
  const [isAuth, setIsAuth] = useState(isAuthenticated());
  const handleLogout = () => {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    setIsAuth(false);
    window.location.href = "/login";
  };

  // список дисциплин
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  // модалка с результатами
  const [modalOpen, setModalOpen] = useState(false);
  const [activeDiscipline, setActiveDiscipline] = useState<string | null>(null);
  const [cardsLoading, setCardsLoading] = useState(false);
  const [cardsError, setCardsError] = useState<string | null>(null);
  const [cardsData, setCardsData] = useState<ChatCardResponse | null>(null);

  // следим за изменением токена в других вкладках
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "token") setIsAuth(isAuthenticated());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // грузим список дисциплин
  useEffect(() => {
    (async () => {
      try {
        setListLoading(true);
        setListError(null);
        const list = await fetchEducationalDisciplineList();
        setDisciplines(list);
      } catch (e: any) {
        setListError(e?.message || "Не удалось загрузить список дисциплин");
        // 401 → вероятно нет авторизации
        if (String(e?.message || "").includes("401")) {
          setTimeout(() => (window.location.href = "/login"), 800);
        }
      } finally {
        setListLoading(false);
      }
    })();
  }, []);

  // по клику на дисциплину запрашиваем карточки
  const openDiscipline = async (discipline: string) => {
    setActiveDiscipline(discipline);
    setCardsLoading(true);
    setCardsError(null);
    setCardsData(null);
    setModalOpen(true);
    try {
      const data = await fetchChatCardsByDiscipline(discipline);
      setCardsData(data);
    } catch (e: any) {
      setCardsError(e?.message || "Не удалось загрузить карточки");
    } finally {
      setCardsLoading(false);
    }
  };

  // сводка по количеству карточек (после открытия модалки)
  const totals = useMemo(() => {
    if (!cardsData) return { v: 0, b: 0, all: 0 };
    const v = cardsData.vector_search?.length || 0;
    const b = cardsData.book_search?.length || 0;
    return { v, b, all: v + b };
  }, [cardsData]);

  return (
    <div className="fixed inset-0 flex flex-col w-full bg-gray-50 overflow-auto">
      <HeaderBar isAuth={isAuth} onLogout={handleLogout} />
      <div className="pt-[72px] pb-16">
        <div className="max-w-6xl mx-auto px-4 py-6 space-y-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={LOGO_URL} alt="TAU Library" className="h-8 w-8 rounded-lg object-contain" />
              <div>
                <h1 className="text-lg md:text-xl font-semibold text-tau-primary">Учебные дисциплины</h1>
                <p className="text-xs text-gray-500">
                  Выберите дисциплину, чтобы получить рекомендации.
                </p>
              </div>
            </div>

            {cardsData && (
              <div className="hidden md:flex items-center gap-2 text-xs text-gray-600">
                <span>Показано: {totals.all}</span>
                <span className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-200">V: {totals.v}</span>
                <span className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-200">B: {totals.b}</span>
              </div>
            )}
          </div>

          {listLoading && <div className="text-center text-gray-500 mt-10">Загрузка списка дисциплин…</div>}
          {listError && <div className="text-center text-red-600 mt-6">{listError}</div>}
          {!listLoading && !listError && disciplines.length === 0 && (
            <div className="text-center text-gray-500 mt-10">Список дисциплин пуст.</div>
          )}

          {!listLoading && !listError && disciplines.length > 0 && (
            <>
              {/* Поиск/фильтр при желании */}
              {/* <div className="max-w-sm">
                <input className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" placeholder="Поиск дисциплины…" />
              </div> */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {disciplines.map((d, idx) => (
                  <button
                    key={`${d}-${idx}`}
                    onClick={() => openDiscipline(d)}
                    className="text-left border border-gray-200 bg-white hover:bg-gray-50 rounded-xl p-3 transition group"
                    title={d}
                  >
                    <div className="flex items-start gap-2">
                      <img src={LOGO_URL} alt="" className="h-7 w-7 rounded-md object-contain" />
                      <div className="text-sm font-medium text-tau-primary line-clamp-3 group-hover:underline">
                        {d}
                      </div>
                    </div>
                    <div className="mt-2 text-[11px] text-gray-500">
                      Нажмите, чтобы получить рекомендации
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <ResultsModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        discipline={activeDiscipline}
        loading={cardsLoading}
        error={cardsError}
        data={cardsData}
      />
    </div>
  );
};

export default RecommendationsPage;
