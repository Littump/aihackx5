import { BlanketLayer, CapLayer, CupLayer, FurLayer, ShelfLayer } from "./DomovoyLayers";
import {
  BoredSymbol,
  CheerfulSymbol,
  CozySymbol,
  HealthySymbol,
  SleepySymbol,
} from "./DomovoyMoodSymbols";

/** Библиотека фигур персонажа, монтируется один раз в корне приложения, чтобы `<use href>` во всех инстансах не дублировал id. */
export function DomovoyDefs() {
  return (
    <svg width="0" height="0" className="absolute" aria-hidden="true">
      <defs>
        <FurLayer />
        <CapLayer />
        <BlanketLayer />
        <CupLayer />
        <ShelfLayer />
        <CheerfulSymbol />
        <CozySymbol />
        <HealthySymbol />
        <BoredSymbol />
        <SleepySymbol />
      </defs>
    </svg>
  );
}
