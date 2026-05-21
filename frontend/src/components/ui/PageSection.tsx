import type { ReactNode } from "react";

type PageSectionProps = {
  actions?: ReactNode;
  children?: ReactNode;
  description?: string;
  eyebrow: string;
  title: string;
};

export function PageSection({
  actions,
  children,
  description,
  eyebrow,
  title,
}: PageSectionProps) {
  return (
    <section className="page-section">
      <div className="content-stack">
        <p className="eyebrow">{eyebrow}</p>
        <div className="page-heading">
          <div>
            <h1>{title}</h1>
            {description ? <p className="lede">{description}</p> : null}
          </div>
          {actions ? <div className="page-actions">{actions}</div> : null}
        </div>
        {children}
      </div>
    </section>
  );
}
