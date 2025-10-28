// src/utils/aiClient.ts

export interface BookCard {
  source: "book_search";
  title: string;
  author?: string;
  pub_info?: string;
  year?: string;
  subjects?: string;
  lang?: string;
  id_book?: string;
  text_snippet?: string;
  summary?: string;
  cover?: string;
  // опционально можно добавить:
  download_url?: string | null;
}

export interface VectorCard {
  source: "vector_search";
  title: string;
  id_book?: string;
  page?: string | null;
  text_snippet?: string;
  download_url?: string | null; // делаем опциональным, чтобы не конфликтовать с остальным кодом
  summary?: string;
}

export type Card = BookCard | VectorCard;

export interface AIResponse {
  reply: string;
  book_search: BookCard[];
  vector_search: VectorCard[];
}

// локальная утилита получения токена, чтобы не тянуть лишние импорты
function getAuthToken(): string {
  return (
    localStorage.getItem("token") ||
    sessionStorage.getItem("token") ||
    ""
  );
}

export async function fetchAIResponse(message: string): Promise<AIResponse> {
  const apiUrl = "/api/chat_card";
  const payload = {
    query: message,
    k: 100,
    sessionId: "web-client",
  };

  const token = getAuthToken();

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    return {
      reply: data.reply || "Ответ не найден.",
      book_search: data.book_search || [],
      vector_search: data.vector_search || [],
    };
  } catch (error) {
    console.error("Ошибка при обращении к AI API:", error);
    return {
      reply: "Произошла ошибка при получении ответа от сервера.",
      book_search: [],
      vector_search: [],
    };
  }
}
