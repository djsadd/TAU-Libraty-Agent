// api.ts
export async function apiFetch(input: RequestInfo, init: RequestInit = {}) {
  const token =
    localStorage.getItem("token") ?? sessionStorage.getItem("token");

  const headers = new Headers(init.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(input, { ...init, headers });
  if (res.status === 401) {
    // токен протух — почистим и отправим на /login
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    // можно ещё refresh попытаться, если используешь refresh_token
    window.location.href = "/login";
    return res;
  }
  return res;
}
