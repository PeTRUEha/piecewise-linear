/** Сквозные сценарии редактора против полного Compose-окружения. */

import {
  expect,
  test,
  type APIRequestContext,
  type Locator,
  type Page,
} from "../../frontend/playwright-support";

interface PointResponse {
  id: number;
}

/** Remove all persisted points through the public API. */
async function clearPoints(request: APIRequestContext, baseURL: string): Promise<void> {
  const response = await request.get(`${baseURL}/api/v1/points`);
  expect(response.ok()).toBe(true);
  const points = (await response.json()) as PointResponse[];
  for (const point of points) {
    const deleted = await request.delete(`${baseURL}/api/v1/points/${String(point.id)}`);
    expect(deleted.ok()).toBe(true);
  }
}

/** Add one point using the visible coordinate form. */
async function addPoint(page: Page, x: string, y: string): Promise<void> {
  const form = page.locator(".add-form");
  await form.locator("input").nth(0).fill(x);
  await form.locator("input").nth(1).fill(y);
  const saved = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/points") && response.request().method() === "POST",
  );
  await form.getByRole("button", { name: "Добавить" }).click();
  expect((await saved).ok()).toBe(true);
}

/** Drag the source handle to the vertical center of a target row. */
async function dragToRow(page: Page, handle: Locator, target: Locator): Promise<void> {
  const sourceBox = await handle.boundingBox();
  const targetBox = await target.boundingBox();
  if (sourceBox === null || targetBox === null) {
    throw new Error("Не удалось определить координаты строк");
  }
  await page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2, {
    steps: 12,
  });
  await page.mouse.up();
}

test.beforeEach(async ({ request, baseURL }) => {
  if (baseURL === undefined) {
    throw new Error("Playwright baseURL is required");
  }
  await clearPoints(request, baseURL);
});

test("adds, edits, reorders and deletes points", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Редактор ломаной" })).toBeVisible();

  await addPoint(page, "1", "1");
  await addPoint(page, "2", "4");
  await addPoint(page, "-1", "3");
  const rows = page.locator(".point-row");
  await expect(rows).toHaveCount(3);

  const firstX = rows.nth(0).locator("input").nth(0);
  const updated = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/points/1") && response.request().method() === "PATCH",
  );
  await firstX.fill("10");
  await firstX.press("Enter");
  expect((await updated).ok()).toBe(true);
  await expect(firstX).toHaveValue("10");

  const reordered = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/points/order") && response.request().method() === "PUT",
  );
  await dragToRow(page, rows.nth(0).getByRole("button", { name: "Перетащить точку 1" }), rows.nth(2));
  expect((await reordered).ok()).toBe(true);
  await expect(rows.nth(0).locator("input").nth(0)).toHaveValue("2");
  await expect(rows.nth(2).locator("input").nth(0)).toHaveValue("10");

  page.once("dialog", async (dialog) => {
    await dialog.accept();
  });
  const deleted = page.waitForResponse(
    (response) => response.url().includes("/api/v1/points/") && response.request().method() === "DELETE",
  );
  await rows.nth(1).getByRole("button", { name: "Удалить точку 2" }).click();
  expect((await deleted).ok()).toBe(true);
  await expect(rows).toHaveCount(2);

  await page.reload();
  await expect(page.locator(".point-row")).toHaveCount(2);
  await expect(page.locator(".point-row").nth(0).locator("input").nth(0)).toHaveValue("2");
  await expect(page.locator(".point-row").nth(1).locator("input").nth(0)).toHaveValue("10");
});

test("keeps the page within a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
  await expect(page.getByRole("heading", { name: "Точки" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ломаная" })).toBeVisible();
});
