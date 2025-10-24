export interface Book {
  title: string;
  author?: string;
  pub_info?: string;
  year?: string;
  id_book?: string;
  text_snippet?: string;
  summary?: string;
  cover?: string;
  source?: string; // добавляем источник: "book_search" или "vector_search"
}

export interface AIResponse {
  reply: string; // текст от LLM
  vector_search?: Book[]; // результаты из векторного поиска
  book_search?: Book[]; // результаты из базы книг
  cards?: Book[]; // поддержка старого поля (чтобы не падало)
}


export async function fetchAIResponse(message: string): Promise<AIResponse> {
  const apiUrl = "/api/chat_card";
  const payload = {
    query: message,
    k: 100,
    sessionId: "web-client",
  };

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) throw new Error(`Ошибка ${response.status}: ${response.statusText}`);

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
