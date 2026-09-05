/** Unit tests for typed API response handling. */

import { afterEach, describe, expect, it, vi } from "vitest";

import { pointsApi } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("pointsApi", () => {
  it("rejects malformed successful payloads", async () => {
    /** Protect application state from an invalid server response. */
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json([{ id: 1, x: "bad", y: 2 }])));

    await expect(pointsApi.list()).rejects.toThrow("Сервер вернул некорректный список точек");
  });

  it("uses a server detail for failed JSON responses", async () => {
    /** Surface the stable error detail returned by the backend. */
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({ detail: "Point set has changed" }, { status: 409 })),
    );

    await expect(pointsApi.reorder([2, 1])).rejects.toThrow("Point set has changed");
  });

  it("reports network failures in user-facing language", async () => {
    /** Translate a rejected fetch into a readable connection error. */
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    await expect(pointsApi.list()).rejects.toThrow("Сервер недоступен");
  });
});
