// Shows a path like "CLD-015 <-[AMENDS]- CLD-015-A1" with the relation names highlighted.

const RELATION = /(<?-\[[A-Z_]+\]->?)/;

export function RelationText({ text }: { text: string }) {
  return (
    <>
      {text.split(RELATION).map((part, i) =>
        RELATION.test(part) ? (
          <span key={i} className="rel">
            {part}
          </span>
        ) : (
          part
        ),
      )}
    </>
  );
}
