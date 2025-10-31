// src/utils/aiClient.ts
function getAuthToken(): string {
  return (
    localStorage.getItem("token") ||
    sessionStorage.getItem("token") ||
    ""
  );
}

/** Универсальный запрос к /api/chat_card_recommendations
 * 1) Пытается GET /api/chat_card_recommendations[/?topics=...]
 * 2) Если 405 — пробует POST /api/chat_card_recommendations[ / ]
 */
export async function fetchChatCardRecommendations(topics?: string[]): Promise<any> {
  const token = getAuthToken();
  const base = "/api/chat_card_recommendations";              // <-- ключевое изменение: добавили /api
  const withTopics = topics && topics.length ? `?topics=${encodeURIComponent(topics.join(","))}` : "";

  // попытка 1: GET без слэша
  let res = await fetch(`${base}${withTopics}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  // если метод не разрешён, пробуем альтернативы
  if (res.status === 405) {
    // попытка 2: GET со слэшем
    res = await fetch(`${base}/${withTopics}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (res.status === 405) {
      // попытка 3: POST без слэша
      res = await fetch(base, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(topics && topics.length ? { topics } : {}),
      });

      if (res.status === 405) {
        // попытка 4: POST со слэшем
        res = await fetch(`${base}/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(topics && topics.length ? { topics } : {}),
        });
      }
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}
