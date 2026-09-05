/** Корневой компонент одностраничного интерфейса. */

import { PointList } from "./PointList";
import { PointPlot } from "./PointPlot";
import { usePoints } from "./usePoints";

export function App() {
  const state = usePoints();
  return (
    <main>
      <header className="hero">
        <div><p className="eyebrow">Piecewise Linear</p><h1>Редактор ломаной</h1><p className="subtitle">Задайте точки, настройте координаты и перетащите их в нужном порядке.</p></div>
        <div className={`save-state ${state.saving ? "is-saving" : ""}`} role="status"><span />{state.saving ? "Сохраняем…" : "Синхронизировано"}</div>
      </header>
      {state.error !== null && <div className="error-banner" role="alert"><span>{state.error}</span><button type="button" onClick={state.clearError} aria-label="Закрыть сообщение">×</button></div>}
      {state.loading ? <div className="loading" role="status">Загружаем точки…</div> : (
        <div className="workspace">
          <PointList points={state.points} disabled={state.saving} onDraft={state.updateDraft} onSave={state.save} onAdd={state.add} onDelete={state.remove} onReorder={state.reorder} />
          <PointPlot points={state.points} />
        </div>
      )}
    </main>
  );
}
