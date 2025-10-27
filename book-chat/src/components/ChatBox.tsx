// ChatBox.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import DOMPurify from "dompurify";

/* ==========================
 * Вспомогательное
 * ========================== */
function isAuthenticated() {
  return !!(localStorage.getItem("token") || sessionStorage.getItem("token"));
}
function getAuthToken() {
  return localStorage.getItem("token") || sessionStorage.getItem("token") || "";
}

/** Универсальный парсер потока:
 * - Oбычный текст: просто накапливаем
 * - NDJSON: каждая строка — JSON; {type:"text", delta:"..."}, {type:"meta", download_url:"..."}
 * - SSE: строки начинаются с "data:"; внутри либо текст, либо JSON
 */
async function streamApi({
  url,
  body,
  onText,
  onDownloadUrl,
  signal,
}: {
  url: string;
  body: unknown;
  onText: (chunk: string) => void;
  onDownloadUrl?: (u: string) => void;
  signal?: AbortSignal;
}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body ?? {}),
    signal,
  });

  if (!resp.ok || !resp.body) {
    const t = await resp.text().catch(() => "");
    throw new Error(`Bad response ${resp.status}: ${t}`);
  }

  const ctype = (resp.headers.get("content-type") || "").toLowerCase();
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();

  let leftover = ""; // для NDJSON/строк

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });

    // SSE?
    if (ctype.includes("text/event-stream")) {
      // Разбиваем по \n\n (окончание event)
      const events = (leftover + chunk).split(/\n\n/);
      leftover = events.pop() || "";
      for (const evt of events) {
        // Ищем строки "data: ..."
        const lines = evt.split(/\n/);
        for (const ln of lines) {
          const m = ln.match(/^data:\s*(.*)$/i);
          if (!m) continue;
          const data = m[1];
          try {
            const j = JSON.parse(data);
            if (j?.type === "text" && typeof j.delta === "string") onText(j.delta);
            else if (j?.type === "meta" && typeof j.download_url === "string") onDownloadUrl?.(j.download_url);
            else if (typeof j === "string") onText(j);
          } catch {
            // не JSON — считаем обычным текстом
            if (data) onText(data);
          }
        }
      }
      continue;
    }

    // NDJSON или «просто текст построчно»
    const combined = leftover + chunk;
    const lines = combined.split(/\r?\n/);
    leftover = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // Пытаемся как JSON
      try {
        const j = JSON.parse(trimmed);
        if (j?.type === "text" && typeof j.delta === "string") onText(j.delta);
        else if (j?.type === "meta" && typeof j.download_url === "string") onDownloadUrl?.(j.download_url);
        else if (typeof j === "string") onText(j);
        else {
          // неизвестный объект — игнорируем
        }
        continue;
      } catch {
        // Не JSON — считаем как кусок обычного текста
        onText(trimmed + "\n");
      }
    }
  }

  // добиваем остатки как текст (если это не SSE и не NDJSON)
  if (leftover && !ctype.includes("text/event-stream")) {
    // Если остаток похож на JSON — попробуем
    try {
      const j = JSON.parse(leftover.trim());
      if (j?.type === "text" && typeof j.delta === "string") onText(j.delta);
      else if (j?.type === "meta" && typeof j.download_url === "string") onDownloadUrl?.(j.download_url);
      else if (typeof j === "string") onText(j);
      else onText(leftover);
    } catch {
      onText(leftover);
    }
  }
}

/* ==========================
 * Типы
 * ========================== */
type Role = "user" | "assistant";
interface Message {
  role: Role;
  text?: string;       // введённый пользователем текст
  streamed?: string;   // накопленный стрим ответа
  download_url?: string | null; // если бэк прислал мету
}

/* ==========================
 * Модалка с отдельным стримом контекста
 * ========================== */
const BookModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  // что отправляем на /api/generate_llm_context
  payload: Record<string, any> | null;
}> = ({ isOpen, onClose, payload }) => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const acRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!isOpen || !payload) return;

    setText("");
    setDownloadUrl(null);
    setLoading(true);

    const ac = new AbortController();
    acRef.current = ac;

    streamApi({
      url: "/api/generate_llm_context",
      body: payload,
      signal: ac.signal,
      onText: (delta) => setText((prev) => prev + delta),
      onDownloadUrl: (u) => setDownloadUrl(u),
    })
      .catch((e) => console.error("ctx stream error:", e))
      .finally(() => setLoading(false));

    return () => {
      ac.abort();
    };
  }, [isOpen, payload]);

  const html = useMemo(() => {
    return DOMPurify.sanitize((text || "").replace(/\n/g, "<br>"));
  }, [text]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl relative border border-gray-200">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-800"
          aria-label="Закрыть"
        >
          ✕
        </button>

        <h2 className="text-lg font-semibold text-gray-900">Контекст</h2>

        <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 min-h-[120px]">
          {loading && (
            <div className="flex items-center gap-2 text-blue-600 mb-2">
              <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce delay-100" />
              <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce delay-200" />
              <span>Генерирую…</span>
            </div>
          )}
          <div dangerouslySetInnerHTML={{ __html: html }} />
        </div>

        {downloadUrl && (
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
          >
            Скачать файл
          </a>
        )}
      </div>
    </div>
  );
};

/* ==========================
 * Основной компонент (только стрим + download_url)
 * ========================== */
export const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isAuth, setIsAuth] = useState(isAuthenticated());

  // модалка
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalPayload, setModalPayload] = useState<Record<string, any> | null>(null);

  const endRef = useRef<HTMLDivElement | null>(null);
  const acRef = useRef<AbortController | null>(null);

  // авто-скролл
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  // если токен изменился в других вкладках
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "token") setIsAuth(isAuthenticated());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // Очистка стримов при размонтировании
  useEffect(() => {
    return () => acRef.current?.abort();
  }, []);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q) return;

    // добавляем сообщение пользователя
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");

    // добавляем пустую "ассистентскую" болванку и стримим внутрь
    const idx = messages.length + 1; // позиция будущего ассистентского сообщения
    setMessages((prev) => [...prev, { role: "assistant", streamed: "", download_url: null }]);

    // обрываем предыдущий стрим, если был
    acRef.current?.abort();
    const ac = new AbortController();
    acRef.current = ac;

    try {
      await streamApi({
        url: "/api/chat_stream",
        body: { query: q },
        signal: ac.signal,
        onText: (delta) => {
          setMessages((prev) => {
            const copy = [...prev];
            const m = copy[idx];
            if (m && m.role === "assistant") {
              m.streamed = (m.streamed || "") + delta;
            }
            return copy;
          });
        },
        onDownloadUrl: (u) => {
          setMessages((prev) => {
            const copy = [...prev];
            const m = copy[idx];
            if (m && m.role === "assistant") {
              m.download_url = u;
            }
            return copy;
          });
        },
      });
    } catch (err) {
      console.error("chat stream error:", err);
      // помечаем ошибку как текст
      setMessages((prev) => {
        const copy = [...prev];
        const m = copy[idx];
        if (m && m.role === "assistant") {
          m.streamed = (m.streamed || "") + "\n[Ошибка при получении ответа]";
        }
        return copy;
      });
    }
  }

  // Запуск модалки со стримом контекста.
  // В payload можно передать всё, что требуется вашему бэку: id_book, title, page, query и т.п.
  function openModalWithContext(payload: Record<string, any>) {
    setModalPayload(payload);
    setIsModalOpen(true);
  }

  function sanitizeHtml(s?: string) {
    return DOMPurify.sanitize((s || "").replace(/\n/g, "<br>"));
  }

  return (
    <div className="fixed inset-0 flex flex-col bg-gray-50">
      {/* Шапка максимально простая */}
      <div className="border-b bg-white/95 backdrop-blur px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="text-sm text-gray-700">
            <span className="font-semibold">Library Chat</span> — только стрим и download_url
          </div>
          <div className="text-xs text-gray-500">{isAuth ? "auth" : "guest"}</div>
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto w-full p-3 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`rounded-2xl px-4 py-2 max-w-[85%] ${
                  m.role === "user" ? "bg-blue-600 text-white" : "bg-white border border-gray-200 text-gray-900"
                }`}
              >
                {m.role === "user" && <div>{m.text}</div>}
                {m.role === "assistant" && (
                  <div className="prose prose-sm max-w-none">
                    <div
                      dangerouslySetInnerHTML={{ __html: sanitizeHtml(m.streamed) }}
                    />
                    {m.download_url && (
                      <div className="mt-3">
                        <a
                          href={m.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition text-xs"
                        >
                          Скачать файл
                        </a>
                      </div>
                    )}

                    {/* Кнопка для открытия модалки стрима контекста:
                       передайте сюда нужные поля вашего бэка */}
                    <div className="mt-2">
                      <button
                        onClick={() =>
                          openModalWithContext({
                            // пример полезной нагрузки; подстройте под ваш бэк
                            title: m.text || "context",
                            // можно прокинуть id_book / page / query
                            // id_book: "...",
                            // page: 12,
                            // query: "..."
                          })
                        }
                        className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 transition"
                      >
                        Открыть контекст (модалка)
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </div>

      {/* Поле ввода */}
      <form onSubmit={sendMessage} className="border-t bg-white px-3 py-3">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Введите запрос…"
            className="flex-1 border border-gray-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition"
          >
            Отправить
          </button>
        </div>
      </form>

      {/* Модалка со стримом контекста */}
      <BookModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        payload={modalPayload}
      />
    </div>
  );
};
