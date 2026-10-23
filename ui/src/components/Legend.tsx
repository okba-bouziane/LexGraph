import { COLORS } from "../config";

/** Colour key for the entity types in the graph. */
export function Legend() {
  return (
    <div className="legend" id="legend">
      {Object.entries(COLORS).map(([type, color]) => (
        <span key={type}>
          <i className="dot" style={{ background: color }} />
          {type}
        </span>
      ))}
    </div>
  );
}
