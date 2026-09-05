/** Согласование оптимистичного состояния точек с backend. */

import { useCallback, useEffect, useRef, useState } from "react";

import { type Point, pointsApi } from "./api";

type Coordinate = "x" | "y";

export function usePoints() {
  const [points, setPoints] = useState<Point[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const confirmed = useRef<Point[]>([]);

  useEffect(() => {
    let active = true;
    void pointsApi
      .list()
      .then((loaded) => {
        if (active) {
          confirmed.current = loaded;
          setPoints(loaded);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Не удалось загрузить точки");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const mutate = useCallback(
    async (optimistic: Point[], operation: () => Promise<Point[]>): Promise<void> => {
      if (saving) {
        return;
      }
      setError(null);
      setPoints(optimistic);
      setSaving(true);
      try {
        const saved = await operation();
        confirmed.current = saved;
        setPoints(saved);
      } catch (reason: unknown) {
        setPoints(confirmed.current);
        setError(reason instanceof Error ? reason.message : "Не удалось сохранить изменение");
      } finally {
        setSaving(false);
      }
    },
    [saving],
  );

  const updateDraft = useCallback((id: number, coordinate: Coordinate, value: number) => {
    setPoints((current) =>
      current.map((point) => (point.id === id ? { ...point, [coordinate]: value } : point)),
    );
  }, []);

  const save = useCallback(
    async (id: number): Promise<void> => {
      const point = points.find((candidate) => candidate.id === id);
      const savedPoint = confirmed.current.find((candidate) => candidate.id === id);
      if (
        point === undefined ||
        savedPoint === undefined ||
        (point.x === savedPoint.x && point.y === savedPoint.y)
      ) {
        return;
      }
      await mutate(points, async () => {
        const updated = await pointsApi.update(id, point.x, point.y);
        return confirmed.current.map((candidate) => (candidate.id === id ? updated : candidate));
      });
    },
    [mutate, points],
  );

  const add = useCallback(
    async (x: number, y: number): Promise<void> => {
      const temporaryId = Math.max(0, ...points.map((point) => point.id)) + 1;
      await mutate([...points, { id: temporaryId, x, y }], async () => {
        const created = await pointsApi.create(x, y);
        return [...confirmed.current, created];
      });
    },
    [mutate, points],
  );

  const remove = useCallback(
    async (id: number): Promise<void> => {
      await mutate(
        points.filter((point) => point.id !== id),
        () => pointsApi.remove(id),
      );
    },
    [mutate, points],
  );

  const reorder = useCallback(
    async (ordered: Point[]): Promise<void> => {
      await mutate(ordered, () => pointsApi.reorder(ordered.map((point) => point.id)));
    },
    [mutate],
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return { points, loading, saving, error, updateDraft, save, add, remove, reorder, clearError };
}
