// src/App.tsx
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import DOMPurify from 'dompurify';
import { v4 as uuidv4 } from 'uuid';

const DEFAULT_API = '/api/chat';

type Role = 'user' | 'assistant';
interface Msg {
  role: Role;
  content: string;
  t: number;
  error?: boolean;
  books?: {
    title: string;
    author?: string;
    year?: number;
    cover?: string;
    description?: string;
  }[];
}


// Компонент для безопасного рендеринга HTML от LLM
function Html({ html }: { html: string }) {
  const clean = useMemo(() => {
    let content = html.trim();

    // Убираем обёртку ```html или ```plaintext
    content = content
      .replace(/^```(?:html|plaintext)?/i, '')
      .replace(/```$/i, '')
      .trim();

    // Превращаем двойные переносы в <p>
    content = content
      .replace(/\n{3,}/g, '\n\n')
      .replace(/\n/g, '<br/>');

    // Санитизация
    const purified = DOMPurify.sanitize(content, {
      ALLOWED_TAGS: [
        'b','strong','i','em','u','s','sup','sub',
        'p','br','hr','blockquote','code','pre','span',
        'ul','ol','li','table','thead','tbody','tr','th','td',
        'a','h1','h2','h3','h4','h5','h6'
      ],
      ALLOWED_ATTR: ['href','title','target','rel','colspan','rowspan'],
      FORBID_TAGS: ['img','figure','picture','source'],   // 👈 добавили
      RETURN_TRUSTED_TYPE: false,
    });


    const tmp = document.createElement('div');
    tmp.innerHTML = purified;
    tmp.querySelectorAll('img, figure, picture, source').forEach(n => n.remove());

    // Ссылки безопасные
    tmp.querySelectorAll('a').forEach(a => {
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener noreferrer');
    });

    // Таблицы — стилизуем
    tmp.querySelectorAll('table').forEach(tbl => {
      tbl.classList.add('ai-table');
    });

    // Убираем пустые <p> и <br> в конце
    // Убираем пустые узлы и <br> в начале и в конце
    tmp.innerHTML = tmp.innerHTML
      .replace(/^(\s|<br\s*\/?>|<p>\s*<\/p>|&nbsp;)+/gi, '')
      .replace(/(\s|<br\s*\/?>|<p>\s*<\/p>|&nbsp;)+$/gi, '');


    return tmp.innerHTML;
  }, [html]);

  return <div className="ai-html" dangerouslySetInnerHTML={{ __html: clean }} />;
}
function BookCard({ book, onOpen }: { book: Msg['books'][0]; onOpen: (b: Msg['books'][0]) => void }) {
  return (
    <button
      type="button"
      className="book-card"
      title="Подробнее"
      // ВАЖНО: открываем на mouseup и гасим всплытие
      onMouseUp={(e) => { e.stopPropagation(); onOpen(book); }}
    >
      <div className="book-info">
        <div className="book-title">{book.title}</div>
        {book.author && <div className="book-author">Автор: {book.author}</div>}
        {book.year && <div className="book-year">{book.year} г.</div>}
        {book.description && <div className="book-desc">{book.description}</div>}
      </div>
    </button>
  );
}

function Modal({
  open,
  onClose,
  book,
}: {
  open: boolean;
  onClose: () => void;
  book?: Msg['books'][0];
}) {
  const mountEl = useMemo(() => {
    const el = document.createElement('div');
    el.className = 'modal-portal';
    return el;
  }, []);

  useEffect(() => {
    document.body.appendChild(mountEl);
    return () => { try { document.body.removeChild(mountEl); } catch {} };
  }, [mountEl]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, [open]);

  const handleOverlayMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!open || !book) return null;

  return createPortal(
    <div className="modal" onMouseDown={handleOverlayMouseDown}>
      <div
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-label={book.title}
        // Блокируем всплытие МЫШИ на диалоге — ключевой момент
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3 className="modal-title">{book.title}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Закрыть">×</button>
        </div>
        <div className="modal-body">
          {book.author && <p><b>Автор:</b> {book.author}</p>}
          {book.year && <p><b>Год:</b> {book.year}</p>}
          {book.description && (<><hr/><p style={{whiteSpace:'pre-wrap'}}>{book.description}</p></>)}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn" onClick={onClose}>Закрыть</button>
        </div>
      </div>
    </div>,
    mountEl
  );
}



export default function App(): JSX.Element {
  const [apiUrl, setApiUrl] = useState<string>(DEFAULT_API);
  const [sessionId, setSessionId] = useState<string>('');
  const [k, setK] = useState<number>(() => Number(localStorage.getItem('k')) || 4);
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
const [selected, setSelected] = useState<Msg['books'][0] | undefined>();
  const [messages, setMessages] = useState<Msg[]>(() => {
    const saved = localStorage.getItem('messages');
    return saved ? (JSON.parse(saved) as Msg[]) : [];
  });
  const chatRef = useRef<HTMLDivElement | null>(null);

  // Генерация уникального sessionId для пользователя
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') setSelected(undefined); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  useEffect(() => {
    let id = sessionStorage.getItem('sessionId');
    if (!id) {
      id = uuidv4();
      sessionStorage.setItem('sessionId', id);
    }
    setSessionId(id);
  }, []);

  // Миграция старых абсолютных значений apiUrl
  useEffect(() => {
    if (apiUrl.startsWith('http')) {
      const next = DEFAULT_API;
      setApiUrl(next);
      localStorage.setItem('apiUrl', next);
    }
  }, []);

  useEffect(() => { localStorage.setItem('k', String(k)); }, [k]);
  useEffect(() => { localStorage.setItem('messages', JSON.stringify(messages)); }, [messages]);
  useEffect(() => { chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' }); }, [messages, loading]);

  const canSend = useMemo(() => question.trim().length > 0 && !loading, [question, loading]);

  async function send(): Promise<void> {
  const q = question.trim();
  if (!q) return;

  setError('');
  setLoading(true);
  setMessages(prev => [...prev, { role: 'user', content: q, t: Date.now() }]);
  setQuestion(''); // очищаем поле

  try {
    const payload = {
      query: q,
      k: Number(k) || 0,
      sessionId,
      context: messages.map(m => ({ role: m.role, content: m.content })).slice(-10) // немного истории
    };

    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data: any = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);

    // Очистим ответ от шумов
    // Очистим ответ от шумов
    let reply = String(data?.reply ?? '')
      .replace(/^```(?:html|plaintext)?/i, '')
      .replace(/```$/i, '')
      .replace(/^\s+|\s+$/g, '') // 💡 убираем пробелы и переносы в начале и конце
      .replace(/^\n+|\n+$/g, '') // 💡 дополнительно чистим лишние переводы
      .trim();

    // Убираем лишние переводы внутри
    reply = reply.replace(/\n{3,}/g, '\n\n');


    // Убираем лишние переводы
    reply = reply.replace(/\n{3,}/g, '\n\n');

        // 💡 Пока API не возвращает книги — используем мок-данные
    const mockBooks = [
      {
        title: 'Менеджмент. Основы и практика',
        author: 'Питер Друкер',
        year: 2019,
        cover: 'https://covers.openlibrary.org/b/id/8231991-L.jpg',
        description: 'Классическое руководство по современному менеджменту.',
        link: '#'
      },
      {
        title: 'Эффективные KPI',
        author: 'Дэвид Парментер',
        year: 2021,
        cover: 'https://covers.openlibrary.org/b/id/8463021-L.jpg',
        description: 'Практическое руководство по разработке ключевых показателей эффективности.',
        link: '#'
      },
    ];

    setMessages(prev => [
      ...prev,
      { role: 'assistant', content: reply, t: Date.now(), books: mockBooks },
    ]);

  } catch (e: unknown) {
    const m = e instanceof Error ? e.message : 'Ошибка запроса';
    setError(m);
    setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${m}`, t: Date.now(), error: true }]);
  } finally {
    setLoading(false);
  }
}


  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>): void {
    if ((e.key === 'Enter' || (e as any).keyCode === 13) && !e.shiftKey) {
      e.preventDefault();
      if (canSend) void send();
    }
  }

  function clearChat(): void { setMessages([]); setError(''); }
    return (
  <div className="container">
    <div className="app">
      {/* === HEADER === */}
      <div className="hdr">
        <div className="brand">
          <div className="logo" />
          <div>
            <div className="title">AI Чат по книгам</div>
            <div className="status">
              ИИ модель: {error ? <span className="pill err">ошибка</span> : <span className="pill ok">готова</span>}
            </div>
          </div>
        </div>
        <div className="toolbar">
          <span className="chip">K документов</span>
          <input
            className="number"
            type="number"
            min={0}
            max={50}
            value={k}
            onChange={e => setK(Number(e.currentTarget.value))}
          />
          <button className="btn" onClick={clearChat} title="Очистить">Очистить</button>
        </div>
      </div>

      {/* === CHAT === */}
      <div className="chat" ref={chatRef}>
        {messages.length === 0 && !loading && (
          <div className="group assistant">
            <div className="meta">Бот • {new Date().toLocaleTimeString()}</div>
            <div className="bubble">
              Задайте вопрос по содержимому загруженных книг. Например: «Где в книге по менеджменту есть про KPI?»
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div className={`group ${m.role}`} key={m.t + ':' + i}>
            <div className="meta">{m.role === 'user' ? 'Вы' : 'Бот'} • {new Date(m.t).toLocaleTimeString()}</div>
            <div className={`bubble ${m.error ? 'err' : ''}`}>
              {m.role === 'assistant' ? (
                <>
                  {m.books && m.books.length > 0 && (
                    <div className="book-list">
                      {m.books.map((b, j) => (
                        <BookCard key={j} book={b} onOpen={setSelected} />
                      ))}
                    </div>
                  )}
                  <Html html={m.content} />
                </>
              ) : (
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{m.content}</pre>
              )}
            </div>
          </div>
        ))}

        {loading && <div className="skeleton" />}
      </div>

      {/* === INPUT ROW === */}
      <div className="row">
        <textarea
          className="textarea"
          rows={2}
          placeholder="Сформулируйте вопрос… (Enter — отправить, Shift+Enter — перенос строки)"
          value={question}
          onChange={e => setQuestion(e.currentTarget.value)}
          onKeyDown={onKeyDown}
        />
        <button className="btn" onClick={() => void send()} disabled={!canSend}>
          {loading ? 'Отправка…' : 'Отправить'}
        </button>
      </div>

      {/* === FOOTER === */}
      <div className="footer">
        <span className="chip">Департамент цифровой трансформации</span>
      </div>
    </div>

    {/* === MODAL === */}
    <Modal open={!!selected} onClose={() => setSelected(undefined)} book={selected} />
  </div>
);
}