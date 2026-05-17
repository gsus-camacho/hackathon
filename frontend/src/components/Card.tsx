import React from "react";

interface Props {
  title?: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  testId?: string;
  className?: string;
}

export const Card: React.FC<Props> = ({ title, description, children, actions, testId, className = "" }) => {
  return (
    <section
      data-testid={testId}
      className={`rounded-xl border border-bio-200 bg-white p-5 transition-all duration-200 ${className}`}
    >
      {(title || actions) && (
        <header className="flex items-start justify-between gap-3 mb-4">
          <div>
            {title && (
              <h2 className="font-heading text-lg font-semibold text-bio-900 tracking-tight">{title}</h2>
            )}
            {description && <p className="text-xs text-bio-500 mt-0.5">{description}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  );
};

export default Card;
