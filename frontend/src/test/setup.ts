/** Общая браузерная среда компонентных тестов. */

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});

class TestResizeObserver implements ResizeObserver {
  /** Start observing a test element. */
  observe(): void {}

  /** Stop observing a test element. */
  unobserve(): void {}

  /** Stop all test observations. */
  disconnect(): void {}
}

globalThis.ResizeObserver = TestResizeObserver;
