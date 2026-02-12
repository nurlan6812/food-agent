'use client';

import { useEffect, useState } from 'react';

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <g clipPath="url(#clip_moon)">
        <path d="M9 18C6.48333 18 4.354 17.129 2.612 15.387C0.870667 13.6457 0 11.5167 0 8.99999C0 6.69999 0.75 4.70399 2.25 3.01199C3.75 1.32066 5.66667 0.333327 8 0.0499939C8.41667 -6.10575e-06 8.74167 0.149994 8.975 0.499994C9.20833 0.849994 9.2 1.21666 8.95 1.59999C8.66667 2.03333 8.454 2.49166 8.312 2.97499C8.17067 3.45833 8.1 3.96666 8.1 4.49999C8.1 5.99999 8.625 7.27499 9.675 8.32499C10.725 9.37499 12 9.89999 13.5 9.89999C14.0167 9.89999 14.5293 9.82499 15.038 9.67499C15.546 9.52499 16 9.31666 16.4 9.04999C16.75 8.81666 17.1083 8.80399 17.475 9.01199C17.8417 9.22066 18 9.54999 17.95 9.99999C17.7167 12.3 16.7377 14.2083 15.013 15.725C13.2877 17.2417 11.2833 18 9 18Z" fill="currentColor"/>
      </g>
      <defs>
        <clipPath id="clip_moon"><rect width="18" height="18" fill="white"/></clipPath>
      </defs>
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="4" fill="currentColor"/>
      <path d="M9 0.5V2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M9 15.5V17.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M2.99 2.99L4.4 4.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M13.6 13.6L15.01 15.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M0.5 9H2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M15.5 9H17.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M2.99 15.01L4.4 13.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M13.6 4.4L15.01 2.99" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    setTheme(initialTheme);
    document.documentElement.classList.toggle('dark', initialTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  return (
    <button
      onClick={toggleTheme}
      className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[#F5F7FA] dark:hover:bg-white/10 transition-colors text-[#89939E]"
      aria-label="테마 전환"
    >
      {theme === 'light' ? <MoonIcon /> : <SunIcon />}
    </button>
  );
}
