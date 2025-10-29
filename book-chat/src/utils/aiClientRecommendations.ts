// src/utils/aiClient.ts
function getAuthToken(): string {
  return (
    localStorage.getItem("token") ||
    sessionStorage.getItem("token") ||
    ""
  );
}

/** Запрос на /chat_card_recommendations
 * Опционально можно передать список тем, если бэк такое поддерживает.
 * Если темы не нужны — вызываем без аргументов.
 */
export async function fetchChatCardRecommendations(topics?: string[]): Promise<any> {
  const token = getAuthToken();
  const res = await fetch("/chat_card_recommendations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(
      topics && topics.length ? { topics } : {}
    ),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}
