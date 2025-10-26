import React, { useEffect, useRef, useState } from "react";

// --- Типы ---
interface Message {
  role: "user" | "assistant";
  text: string;
}

// --- Компонент пузыря сообщения ---
const Bubble: React.FC<Message> = ({ role, text }) => (
  <div
    className={`p-3 rounded-xl max-w-[80%] my-1 ${
      role === "user"
        ? "bg-blue-500 text-white self-end"
        : "bg-gray-200 text-black self-start"
    }`}
  >
    {text}
  </div>
);

// --- Основной компонент с автоскроллом ---
export const MessageBubble: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Привет! Я твой помощник 😊" },
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Автопрокрутка вниз при каждом новом сообщении
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Добавление новых сообщений
  const handleAddMessage = () => {
    setMessages((prev) => [
      ...prev,
      { role: "user", text: "Загружаю данные..." },
      { role: "assistant", text: "✅ Данные успешно загружены!" },
    ]);
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100 overflow-hidden">
      {/* Область сообщений с прокруткой */}
      <div className="flex flex-col h-[70vh] w-full max-w-[500px] overflow-hidden bg-white rounded-lg shadow-inner min-h-0">
        <div
          className="flex-1 overflow-y-auto p-4 min-h-0"
          style={{ WebkitOverflowScrolling: "touch" }}
        >
          {messages.map((msg, idx) => (
            <Bubble key={idx} role={msg.role} text={msg.text} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Кнопка добавления сообщений */}
      <button
        onClick={handleAddMessage}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Загрузить данные
      </button>
    </div>
  );
};

export default MessageBubble;
