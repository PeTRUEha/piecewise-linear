/** Редактируемый и перетаскиваемый список точек. */
/* eslint-disable react-hooks/refs -- dnd-kit exposes callback refs and listeners for rendering. */

import {
  DndContext,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useState, type KeyboardEvent, type SyntheticEvent } from "react";

import type { Point } from "./api";

interface PointListProps {
  points: Point[];
  disabled: boolean;
  onDraft: (id: number, coordinate: "x" | "y", value: number) => void;
  onSave: (id: number) => Promise<void>;
  onAdd: (x: number, y: number) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onReorder: (points: Point[]) => Promise<void>;
}

interface PointRowProps {
  point: Point;
  disabled: boolean;
  onDraft: PointListProps["onDraft"];
  onSave: PointListProps["onSave"];
  onDelete: PointListProps["onDelete"];
}

function PointRow({ point, disabled, onDraft, onSave, onDelete }: PointRowProps) {
  const sortable = useSortable({ id: point.id, disabled });
  const style = {
    transform: CSS.Transform.toString(sortable.transform),
    transition: sortable.transition,
  };

  const updateCoordinate = (coordinate: "x" | "y", value: string) => {
    const numeric = Number(value);
    if (value.trim() !== "" && Number.isFinite(numeric)) {
      onDraft(point.id, coordinate, numeric);
    }
  };

  const finishEditing = async () => {
    await onSave(point.id);
  };

  const handleEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.currentTarget.blur();
    }
  };

  const confirmDelete = async () => {
    if (window.confirm(`Удалить точку ${String(point.id)}?`)) {
      await onDelete(point.id);
    }
  };

  return (
    <li ref={sortable.setNodeRef} style={style} className="point-row">
      <button
        className="drag-handle"
        type="button"
        aria-label={`Перетащить точку ${String(point.id)}`}
        disabled={disabled}
        {...sortable.attributes}
        {...sortable.listeners}
      >
        <span aria-hidden="true">⠿</span>
      </button>
      <span className="point-id">{point.id}</span>
      <label>
        <span>x</span>
        <input
          type="number"
          step="any"
          value={point.x}
          disabled={disabled}
          onChange={(event) => { updateCoordinate("x", event.target.value); }}
          onBlur={() => void finishEditing()}
          onKeyDown={handleEnter}
        />
      </label>
      <label>
        <span>y</span>
        <input
          type="number"
          step="any"
          value={point.y}
          disabled={disabled}
          onChange={(event) => { updateCoordinate("y", event.target.value); }}
          onBlur={() => void finishEditing()}
          onKeyDown={handleEnter}
        />
      </label>
      <button
        className="delete-button"
        type="button"
        aria-label={`Удалить точку ${String(point.id)}`}
        disabled={disabled}
        onClick={() => void confirmDelete()}
      >
        ×
      </button>
    </li>
  );
}

export function PointList(props: PointListProps) {
  const { points, disabled, onDraft, onSave, onAdd, onDelete, onReorder } = props;
  const [newX, setNewX] = useState("");
  const [newY, setNewY] = useState("");
  const sensors = useSensors(
    useSensor(MouseSensor),
    useSensor(TouchSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    const x = Number(newX);
    const y = Number(newY);
    if (newX.trim() === "" || newY.trim() === "" || !Number.isFinite(x) || !Number.isFinite(y)) {
      return;
    }
    await onAdd(x, y);
    setNewX("");
    setNewY("");
  };

  const handleDragEnd = ({ active, over }: DragEndEvent) => {
    if (over === null || active.id === over.id) {
      return;
    }
    const oldIndex = points.findIndex((point) => point.id === active.id);
    const newIndex = points.findIndex((point) => point.id === over.id);
    if (oldIndex >= 0 && newIndex >= 0) {
      void onReorder(arrayMove(points, oldIndex, newIndex));
    }
  };

  return (
    <section className="panel list-panel" aria-labelledby="points-heading">
      <div className="panel-heading">
        <div><p className="eyebrow">Данные</p><h2 id="points-heading">Точки</h2></div>
        <span className="point-count">{points.length}</span>
      </div>
      <form className="add-form" onSubmit={(event) => void handleSubmit(event)}>
        <label><span>x</span><input required type="number" step="any" placeholder="0" value={newX} disabled={disabled} onChange={(event) => { setNewX(event.target.value); }} /></label>
        <label><span>y</span><input required type="number" step="any" placeholder="0" value={newY} disabled={disabled} onChange={(event) => { setNewY(event.target.value); }} /></label>
        <button type="submit" disabled={disabled || newX === "" || newY === ""}>Добавить</button>
      </form>
      {points.length === 0 ? (
        <div className="empty-list">Добавьте первую точку, чтобы построить ломаную.</div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={points.map((point) => point.id)} strategy={verticalListSortingStrategy}>
            <ol className="point-list">
              {points.map((point) => <PointRow key={point.id} point={point} disabled={disabled} onDraft={onDraft} onSave={onSave} onDelete={onDelete} />)}
            </ol>
          </SortableContext>
        </DndContext>
      )}
    </section>
  );
}
