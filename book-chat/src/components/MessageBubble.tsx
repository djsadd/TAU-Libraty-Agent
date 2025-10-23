import React, { useState } from "react";
import { MessageBubble } from "./components/MessageBubble";

export default function App() {
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; text: string }[]>([]);

  const sendMessage = async (text: string) => {
    // здесь логика отправки запроса и добавления сообщений
  };

  return (
    <div className="flex flex-col h-screen p-4 bg-gray-50">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-lg font-semibold">Чат с ИИ</h1>
        {/* ✅ Кнопка очистки */}
        <button
          onClick={() => setMessages([])}
          className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition"
        >
          Очистить
        </button>
      </div>

      {/* Сообщения */}
      <div className="flex flex-col gap-2 flex-grow overflow-y-auto p-2">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} role={msg.role} text={msg.text} />
        ))}
      </div>

      {/* Здесь может быть поле ввода */}
    </div>
  );
}
