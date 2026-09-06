/** Экспорт Playwright для E2E-сценариев за пределами npm-пакета frontend. */

export { expect, test } from "@playwright/test";
export type { APIRequestContext, Locator, Page } from "@playwright/test";
