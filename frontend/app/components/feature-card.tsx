'use client';

import { ReactNode } from 'react';

interface FeatureCardProps {
  icon: ReactNode;
  label: string;
  description: string;
  onClick: () => void;
}

export function FeatureCard({ icon, label, description, onClick }: FeatureCardProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 bg-white rounded-[100px] px-4 py-3 sm:py-4 shadow-sm hover:shadow-md transition-shadow active:scale-[0.98] w-full text-left"
    >
      <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
        {icon}
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-base font-semibold text-[#4D4D4D]">{label}</span>
        <span className="text-xs font-medium text-[#89939E] truncate">{description}</span>
      </div>
    </button>
  );
}
