/** Компонентные сценарии основных состояний редактора. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { pointsApi } from "./api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("shows loading and empty states", async () => {
    /** Render the empty editor after the initial request completes. */
    vi.spyOn(pointsApi, "list").mockResolvedValue([]);

    render(<App />);

    expect(screen.getByText("Загружаем точки…")).toBeInTheDocument();
    expect(await screen.findByText("Добавьте первую точку, чтобы построить ломаную.")).toBeInTheDocument();
    expect(screen.getByText("График появится после добавления точки")).toBeInTheDocument();
  });

  it("adds a point from the coordinate form", async () => {
    /** Submit numeric coordinates and render the confirmed point. */
    const user = userEvent.setup();
    vi.spyOn(pointsApi, "list").mockResolvedValue([]);
    vi.spyOn(pointsApi, "create").mockResolvedValue({ id: 1, x: -2.5, y: 4 });
    render(<App />);
    await screen.findByText("Добавьте первую точку, чтобы построить ломаную.");
    const inputs = screen.getAllByRole("spinbutton");
    const newX = inputs[0];
    const newY = inputs[1];
    if (newX === undefined || newY === undefined) {
      throw new Error("Форма координат не найдена");
    }

    await user.type(newX, "-2.5");
    await user.type(newY, "4");
    await user.click(screen.getByRole("button", { name: "Добавить" }));

    await waitFor(() => {
      expect(pointsApi.create).toHaveBeenCalledWith(-2.5, 4);
    });
    expect(await screen.findByRole("button", { name: "Удалить точку 1" })).toBeInTheDocument();
  });

  it("rolls an optimistic coordinate back after an API error", async () => {
    /** Restore confirmed coordinates and expose a readable error message. */
    vi.spyOn(pointsApi, "list").mockResolvedValue([{ id: 1, x: 1, y: 2 }]);
    vi.spyOn(pointsApi, "update").mockRejectedValue(new Error("Сохранение недоступно"));
    render(<App />);
    await screen.findByRole("button", { name: "Удалить точку 1" });
    const rowX = screen.getAllByRole("spinbutton")[2] as HTMLInputElement;

    fireEvent.change(rowX, { target: { value: "9" } });
    expect(rowX.value).toBe("9");
    fireEvent.blur(rowX);

    expect(await screen.findByRole("alert")).toHaveTextContent("Сохранение недоступно");
    await waitFor(() => {
      expect(rowX.value).toBe("1");
    });
  });

  it("deletes a point only after confirmation", async () => {
    /** Confirm destructive intent before calling the delete endpoint. */
    const user = userEvent.setup();
    vi.spyOn(pointsApi, "list").mockResolvedValue([{ id: 1, x: 1, y: 2 }]);
    vi.spyOn(pointsApi, "remove").mockResolvedValue([]);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Удалить точку 1" }));

    expect(confirm).toHaveBeenCalledWith("Удалить точку 1?");
    await waitFor(() => {
      expect(pointsApi.remove).toHaveBeenCalledWith(1);
    });
    expect(await screen.findByText("Добавьте первую точку, чтобы построить ломаную.")).toBeInTheDocument();
  });
});
