// src/utils/aiClient.ts

export interface Book {
  title: string;
  author: string;
  page?: string | null;
  id_book: string;
  text_snippet?: string;
  summary: string;
  cover?: string;
  source?: string; // ✅ добавь это
}

export interface Source {
  title?: string;
  link?: string;
  id?: string;
  snippet?: string;
}

export interface AIResponse {
  reply: string;
  cards: Book[];
  source?: Source[]; // добавляем поддержку источников
}

export async function fetchAIResponse(message: string): Promise<AIResponse> {
  const apiUrl = "http://192.168.115.214:8000/api/chat_card"; // URL FastAPI

  const payload = {
    query: message,
    k: 5,
    sessionId: "web-client", // можно заменить на реальный sessionId
  };

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // ожидаем, что API возвращает JSON формата { reply, cards, source }
    return {
      reply: data.reply || "Ответ не найден.",
      cards: data.cards || [],
      source: data.source || [], // извлекаем source, если он есть
    };
  } catch (error) {
    console.error("Ошибка при обращении к AI API:", error);
    return {
      reply: "Произошла ошибка при получении ответа от сервера.",
      cards: [],
      source: [],
    };
  }
}
