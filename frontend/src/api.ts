/** Типизированный клиент HTTP API точек. */

export interface Point {
  id: number;
  x: number;
  y: number;
}

interface ApiErrorBody {
  detail?: unknown;
}

function isPoint(value: unknown): value is Point {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    Number.isInteger(candidate.id) &&
    typeof candidate.x === "number" &&
    Number.isFinite(candidate.x) &&
    typeof candidate.y === "number" &&
    Number.isFinite(candidate.y)
  );
}

function parsePoint(value: unknown): Point {
  if (!isPoint(value)) {
    throw new Error("Сервер вернул некорректную точку");
  }
  return value;
}

function parsePoints(value: unknown): Point[] {
  if (!Array.isArray(value) || !value.every(isPoint)) {
    throw new Error("Сервер вернул некорректный список точек");
  }
  return value;
}

function parseErrorMessage(value: unknown, status: number): string {
  if (typeof value === "object" && value !== null) {
    const { detail } = value as ApiErrorBody;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return `Ошибка запроса (${String(status)})`;
}

async function request<T>(
  path: string,
  parser: (value: unknown) => T,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...init,
      headers: init?.body === undefined ? init?.headers : { "Content-Type": "application/json" },
    });
  } catch {
    throw new Error("Сервер недоступен. Проверьте подключение и повторите попытку");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`Сервер недоступен или вернул ошибку (${String(response.status)})`);
    }
    throw new Error("Сервер вернул ответ в неизвестном формате");
  }
  if (!response.ok) {
    throw new Error(parseErrorMessage(payload, response.status));
  }
  return parser(payload);
}

export const pointsApi = {
  list: () => request("/points", parsePoints),
  create: (x: number, y: number) =>
    request("/points", parsePoint, {
      method: "POST",
      body: JSON.stringify({ x, y }),
    }),
  update: (id: number, x: number, y: number) =>
    request(`/points/${String(id)}`, parsePoint, {
      method: "PATCH",
      body: JSON.stringify({ x, y }),
    }),
  remove: (id: number) => request(`/points/${String(id)}`, parsePoints, { method: "DELETE" }),
  reorder: (ids: number[]) =>
    request("/points/order", parsePoints, {
      method: "PUT",
      body: JSON.stringify({ ids }),
    }),
};
