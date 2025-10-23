// src/components/MessageBubble.tsx
import React from "react";

interface MessageBubbleProps {
  role: "user" | "assistant";
  text: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ role, text }) => (
  <div
    className={`p-3 rounded-xl max-w-[80%] ${
      role === "user"
        ? "bg-blue-500 text-white self-end"
        : "bg-gray-200 text-black self-start"
    }`}
  >
    {text}
  </div>
);
