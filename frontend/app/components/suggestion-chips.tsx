'use client';

interface SuggestionChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
}

function ArrowForwardIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="flex-shrink-0">
      <path d="M12 4L10.59 5.41L16.17 11H4V13H16.17L10.59 18.59L12 20L20 12L12 4Z" fill="#89939E" />
    </svg>
  );
}

export function SuggestionChips({ suggestions, onSelect }: SuggestionChipsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="bg-white rounded-3xl px-4 py-4 shadow-sm">
      <p className="text-sm font-bold text-[#212121] mb-3">
        💡 이런 정보는 어떠세요?
      </p>
      <div className="flex flex-col gap-2">
        {suggestions.map((suggestion, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(suggestion)}
            className="w-full flex items-center justify-between bg-[#F5F7FA] text-[#4D4D4D] text-sm px-5 py-2.5 rounded-[45px] hover:bg-[#EBEEF2] active:scale-[0.98] transition-all text-left"
          >
            <span>{suggestion}</span>
            <ArrowForwardIcon />
          </button>
        ))}
      </div>
    </div>
  );
}
