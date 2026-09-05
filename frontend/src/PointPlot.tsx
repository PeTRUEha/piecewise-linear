/** Координатная плоскость с ломаной по порядку точек. */

import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

import type { Point } from "./api";

export function PointPlot({ points }: { points: Point[] }) {
  return (
    <section className="panel plot-panel" aria-labelledby="plot-heading">
      <div className="panel-heading">
        <div><p className="eyebrow">Визуализация</p><h2 id="plot-heading">Ломаная</h2></div>
        <span className="plot-legend"><i /> порядок ID</span>
      </div>
      <div className="plot-area">
        {points.length === 0 ? (
          <div className="empty-plot"><span aria-hidden="true">⌁</span><p>График появится после добавления точки</p></div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 18, right: 18, bottom: 12, left: 0 }}>
              <CartesianGrid stroke="#dbe3ea" strokeDasharray="3 5" />
              <XAxis type="number" dataKey="x" name="x" domain={["auto", "auto"]} />
              <YAxis type="number" dataKey="y" name="y" domain={["auto", "auto"]} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={points} fill="#e45b35" line={{ stroke: "#193d52", strokeWidth: 2 }} />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
