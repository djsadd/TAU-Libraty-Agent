// src/App.tsx
import React, { useEffect, useMemo, useRef, useState } from 'react';

const DEFAULT_API = '/api/chat';

type Role = 'user' | 'assistant';
interface Msg { role: Role; content: string; t: number; error?: boolean }

export default function App(): JSX.Element {
  const [apiUrl, setApiUrl] = useState<string>(() => localStorage.getItem('apiUrl') || DEFAULT_API);
  const [k, setK] = useState<number>(() => Number(localStorage.getItem('k')) || 4);
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [messages, setMessages] = useState<Msg[]>(() => {
    const saved = localStorage.getItem('messages');
    return saved ? (JSON.parse(saved) as Msg[]) : [];
  });
  const chatRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
      if (apiUrl.startsWith('http')) { // миграция со старых абсолютных значений
        const next = '/api/chat';
        setApiUrl(next);
        localStorage.setItem('apiUrl', next);
      }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    setQuestion('');

    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, k: Number(k) || 0 })
      });
      const data: any = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
      const reply = (data?.reply ?? '') as string;
      setMessages(prev => [...prev, { role: 'assistant', content: String(reply), t: Date.now() }]);
    } catch (e: unknown) {
      const m = e instanceof Error ? e.message : 'Ошибка запроса';
      setError(m);
      setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${m}`, t: Date.now(), error: true }]);
    } finally { setLoading(false); }
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
            <input className="number" type="number" min={0} max={50} value={k} onChange={e => setK(Number(e.currentTarget.value))} />

            <button className="btn" onClick={clearChat} title="Очистить">Очистить</button>
          </div>
        </div>

        <div className="chat" ref={chatRef}>
          {messages.length === 0 && !loading && (
            <div className="group assistant">
              <div className="meta">Бот • {new Date().toLocaleTimeString()}</div>
              <div className="bubble">Задайте вопрос по содержимому загруженных книг. Например: «Где в книге по менеджменту есть про KPI?»</div>
            </div>
          )}

          {messages.map((m, i) => (
            <div className={`group ${m.role}`} key={m.t + ':' + i}>
              <div className="meta">{m.role === 'user' ? 'Вы' : 'Бот'} • {new Date(m.t).toLocaleTimeString()}</div>
              <div className="bubble">{m.content}</div>
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
