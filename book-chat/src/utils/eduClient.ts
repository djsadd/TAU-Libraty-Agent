// src/utils/eduClient.ts

function getAuthToken(): string {
  return (
    localStorage.getItem("token") ||
    sessionStorage.getItem("token") ||
    ""
  );
}

/** Получение списка учебных дисциплин текущего пользователя
 * Ожидаемый ответ бэкенда:
 * { "educational_disciplines": string[] }
 */
export async function fetchEducationalDisciplineList(): Promise<string[]> {
  const token = getAuthToken();
  const res = await fetch("/api/educational_discipline_list", {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }

  const data = await res.json();
  const list: unknown = data?.educational_disciplines;
  if (!Array.isArray(list)) {
    throw new Error("Неверный формат ответа: поле educational_disciplines отсутствует или не массив");
  }
  return list as string[];
}

/** Вызов чата с карточками по конкретной дисциплине
 * Передаём query = <discipline>. Остальные поля — по желанию.
 * Ожидаемый ответ бэкенда: { reply, vector_search: Book[], book_search: Book[] }
 */
export interface ChatCardBook {
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
  download_url?: string | null;
  page?: string | null;
}

export interface ChatCardResponse {
  reply: string;
  vector_search?: ChatCardBook[];
  book_search?: ChatCardBook[];
}

export async function fetchChatCardsByDiscipline(discipline: string): Promise<ChatCardResponse> {
  const token = getAuthToken();

  const res = await fetch("/api/chat_card", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      query: discipline,
      // при необходимости можно передавать sessionId, history и пр.
      // sessionId: "recommendations",
      // history: [],
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }

  return res.json();
}
