type PagePlaceholderProps = {
  title: string;
  eyebrow: string;
};

export function PagePlaceholder({ title, eyebrow }: PagePlaceholderProps) {
  return (
    <section className="placeholder-page">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
    </section>
  );
}
