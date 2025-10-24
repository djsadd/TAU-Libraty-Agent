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
}

export interface VectorCard {
  source: "vector_search";
  title: string;
  id_book?: string;
  page?: string | null;
  text_snippet?: string;
  summary?: string;
}

export type Card = BookCard | VectorCard;

export interface AIResponse {
  reply: string;
  book_cards?: BookCard[];
  vector_cards?: VectorCard[];
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
