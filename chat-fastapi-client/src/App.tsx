// src/App.tsx
import React, { useEffect, useMemo, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import { v4 as uuidv4 } from 'uuid';

const DEFAULT_API = '/api/chat';

type Role = 'user' | 'assistant';
interface Msg { role: Role; content: string; t: number; error?: boolean }

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
        'b', 'strong', 'i', 'em', 'u', 's', 'sup', 'sub',
        'p', 'br', 'hr', 'blockquote', 'code', 'pre', 'span',
        'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'img', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
      ],
      ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'src', 'alt', 'colspan', 'rowspan'],
      RETURN_TRUSTED_TYPE: false,
    });

    const tmp = document.createElement('div');
    tmp.innerHTML = purified;

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
    tmp.innerHTML = tmp.innerHTML.replace(/(<p>\s*<\/p>|<br\s*\/?>)+$/g, '');

    return tmp.innerHTML;
  }, [html]);

  return <div className="ai-html" dangerouslySetInnerHTML={{ __html: clean }} />;
}


export default function App(): JSX.Element {
  const [apiUrl, setApiUrl] = useState<string>(DEFAULT_API);
  const [sessionId, setSessionId] = useState<string>('');
  const [k, setK] = useState<number>(() => Number(localStorage.getItem('k')) || 4);
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [messages, setMessages] = useState<Msg[]>(() => {
    const saved = localStorage.getItem('messages');
    return saved ? (JSON.parse(saved) as Msg[]) : [];
  });
  const chatRef = useRef<HTMLDivElement | null>(null);

  // Генерация уникального sessionId для пользователя
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
    let reply = String(data?.reply ?? '')
      .replace(/^```(?:html|plaintext)?/i, '')
      .replace(/```$/i, '')
      .trim();

    // Убираем лишние переводы
    reply = reply.replace(/\n{3,}/g, '\n\n');

    setMessages(prev => [...prev, { role: 'assistant', content: reply, t: Date.now() }]);
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
            <input className="number" type="number" min={0} max={50} value={k}
                   onChange={e => setK(Number(e.currentTarget.value))} />
            <button className="btn" onClick={clearChat} title="Очистить">Очистить</button>
          </div>
        </div>

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
                  <Html html={m.content} />
                ) : (
                  <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{m.content}</pre>
                )}
              </div>
            </div>
          ))}

          {loading && <div className="skeleton" />}
        </div>

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
        <div className="footer">
          <span className="chip">Департамент цифровой трансформации</span>
        </div>
      </div>
    </div>
  );
}
