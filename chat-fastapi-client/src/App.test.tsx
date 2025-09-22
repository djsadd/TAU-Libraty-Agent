import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import App from './App';


const mockFetch = (body: any, ok = true, status = 200) => vi.fn().mockResolvedValue({ ok, status, json: async () => body } as unknown as Response);


describe('Pretty Chat UI', () => {
beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());


it('renders branded header and input', () => {
render(<App />);
expect(screen.getByText('AI Чат по книгам')).toBeInTheDocument();
expect(screen.getByPlaceholderText('Сформулируйте вопрос… (Enter — отправить, Shift+Enter — перенос строки)')).toBeInTheDocument();
});


it('sends a message and shows assistant reply', async () => {
vi.spyOn(globalThis, 'fetch').mockImplementation(mockFetch({ reply: 'Ответ из модели' }) as any);
render(<App />);
const ta = screen.getByPlaceholderText('Сформулируйте вопрос… (Enter — отправить, Shift+Enter — перенос строки)');
fireEvent.change(ta, { target: { value: 'Что такое KPI?' } });
fireEvent.keyDown(ta, { key: 'Enter', code: 'Enter', charCode: 13 });
await waitFor(() => expect(screen.getByText('Ответ из модели')).toBeInTheDocument());
});


it('propagates k to backend', async () => {
const spy = vi.spyOn(globalThis, 'fetch').mockImplementation(mockFetch({ reply: 'ok' }) as any);
render(<App />);
const kField = screen.getByDisplayValue('4');
fireEvent.change(kField, { target: { value: '2' } });
const ta = screen.getByPlaceholderText('Сформулируйте вопрос… (Enter — отправить, Shift+Enter — перенос строки)');
fireEvent.change(ta, { target: { value: 'test' } });
fireEvent.keyDown(ta, { key: 'Enter', code: 'Enter', charCode: 13 });
await waitFor(() => expect(spy).toHaveBeenCalled());
const [, init] = spy.mock.calls[0];
const sent = JSON.parse((init as RequestInit).body as string);
expect(sent.k).toBe(2);
expect(sent.query).toBe('test');
});


it('shows error bubble on API failure', async () => {
vi.spyOn(globalThis, 'fetch').mockImplementation(mockFetch({ error: 'Internal error' }, false, 500) as any);
render(<App />);
const ta = screen.getByPlaceholderText('Сформулируйте вопрос… (Enter — отправить, Shift+Enter — перенос строки)');
fireEvent.change(ta, { target: { value: 'oops' } });
fireEvent.keyDown(ta, { key: 'Enter', code: 'Enter', charCode: 13 });
await waitFor(() => expect(screen.getByText(/⚠️/)).toBeInTheDocument());
});
});