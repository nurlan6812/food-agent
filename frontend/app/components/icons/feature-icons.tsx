interface IconProps {
  size?: number;
  className?: string;
}

// 사진으로 음식점 찾기 - 카메라 (노랑/주황)
export function CameraIcon({ size = 32, className = '' }: IconProps) {
  return (
    <svg width={size} height={size * 0.8} viewBox="0 0 32 26" fill="none" className={className}>
      <path d="M0 0H32V25.6H0V0Z" fill="#FFE736"/>
      <path d="M6.40003 9.6C8.16734 9.6 9.60003 8.16732 9.60003 6.4C9.60003 4.63269 8.16734 3.2 6.40003 3.2C4.63272 3.2 3.20003 4.63269 3.20003 6.4C3.20003 8.16732 4.63272 9.6 6.40003 9.6Z" fill="#FF9E2F"/>
      <path d="M3.20003 22.4H28.8V3.2L16 16H9.60003L3.20003 22.4Z" fill="#FF9E2F"/>
    </svg>
  );
}

// 맛집 및 식당 검색 - 면류 (PNG 이미지 사용)
export function NoodleIcon({ size = 32, className = '' }: IconProps) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/icons/icon-noodles.png"
      alt=""
      width={size}
      height={size}
      className={className}
      style={{ width: size, height: size, objectFit: 'contain' }}
    />
  );
}

// 레시피 검색 - 책 (초록)
export function RecipeIcon({ size = 32, className = '' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" className={className}>
      <path d="M16 5V27C16 24.7999 14.1999 23 12 23H0V1H12C14.2091 1 16 2.79087 16 5Z" fill="#4DE600"/>
      <path d="M16 27H0V23H12C14.1999 23 16 24.7999 16 27Z" fill="#00CC00"/>
      <path d="M16 5V27C16 24.7999 17.8001 23 20 23H32V1H20C17.7909 1 16 2.79087 16 5Z" fill="#4DE600"/>
      <path d="M16 27H32V23H20C17.8001 23 16 24.7999 16 27Z" fill="#00CC00"/>
      <path d="M4 5H12V7H4V5Z" fill="#C8FA64"/>
      <path d="M4 11H12V13H4V11Z" fill="#C8FA64"/>
      <path d="M4 17H12V19H4V17Z" fill="#C8FA64"/>
      <path d="M20 5H28V7H20V5Z" fill="#C8FA64"/>
      <path d="M20 11H28V13H20V11Z" fill="#C8FA64"/>
      <path d="M20 17H28V19H20V17Z" fill="#C8FA64"/>
      <path d="M28 31L25 29L22 31V27H28V31Z" fill="#4DE600"/>
      <path d="M22 23H28V27H22V23Z" fill="#009800"/>
    </svg>
  );
}

// 영양정보 및 칼로리 - 파이차트 (핑크)
export function NutritionIcon({ size = 32, className = '' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" className={className}>
      <g clipPath="url(#clip_pie)">
        <path d="M32 17C32 21.6799 30.1 25.9399 27.02 29.02L25.6 27.5799L19.9399 21.9199C19.9599 21.8799 20 21.8599 20 21.8399C20.4599 21.38 20.8399 20.88 21.14 20.3199C21.14 20.28 22 18.98 22 17C22 13.8399 19.88 11.1599 17 10.2999L15 2V0C24.38 0 32 7.62 32 17Z" fill="#FF8DE4"/>
        <path d="M15 2L17 6.14994L15 10C11.14 10 8 13.14 8 17L4 19L0 17C0 8.72 6.72 2 15 2Z" fill="#FF4DB3"/>
        <path d="M8 17H0C0 25.2843 6.71569 32 15 32V24C11.1406 24 8 20.8594 8 17Z" fill="#FF8DE4"/>
        <path d="M17 2.14V10.2999C16.5401 10.1599 16.0799 10.0599 15.6 10.0399C15.4001 10.0201 15.2 10 15 10V2C15.6801 2 16.3399 2.05994 17 2.14Z" fill="#FF0068"/>
      </g>
      <defs>
        <clipPath id="clip_pie"><rect width="32" height="32" fill="white"/></clipPath>
      </defs>
    </svg>
  );
}

// 식당 리뷰 요약 - 리뷰 캐릭터 (보라)
export function ReviewIcon({ size = 32, className = '' }: IconProps) {
  const h = size * (38 / 32);
  return (
    <svg width={size} height={h} viewBox="0 0 32 38" fill="none" className={className}>
      <path d="M32 16C32 22.6462 27.9384 28.3568 22.1538 30.7692L19.6923 31.5569C18.5108 31.8523 17.2801 32 16 32C14.7199 32 13.4892 31.8523 12.3077 31.5569L9.84615 30.7692C4.06162 28.3568 0 22.6462 0 16C0 7.163 7.163 0 16 0C24.837 0 32 7.163 32 16Z" fill="#E5C9FF"/>
      <path d="M12.3077 31.5569V37.3846H9.84619V30.7693L12.3077 31.5569Z" fill="#D580FF"/>
      <path d="M22.1539 30.7693V37.3846H19.6923V31.5569L22.1539 30.7693Z" fill="#D580FF"/>
      <path d="M15.3846 6.20824L16.3759 5.25795C17.6977 3.99094 19.8407 3.99094 21.1625 5.25795C22.4843 6.52496 22.4843 8.57913 21.1625 9.84614L15.3846 15.3846L9.60673 9.84624C8.28494 8.57923 8.28494 6.52507 9.60673 5.25805C10.9285 3.99104 13.0715 3.99104 14.3933 5.25805L15.3846 6.20824Z" fill="#9966FF"/>
      <path d="M14.7692 20.9231C14.7692 23.6061 13.7355 25.8461 12.3077 26.7076V31.5569C11.4462 31.3599 10.6338 31.1138 9.84615 30.7692V26.7076C8.41838 25.8461 7.38461 23.6061 7.38461 20.9231C7.38461 17.5261 8.95682 16.6923 11 16.6923C13.0431 16.6923 14.7692 17.5261 14.7692 20.9231Z" fill="#9966FF"/>
      <path d="M24.6154 16.7692V24.6154C24.6154 25.9692 23.5077 27.0769 22.1539 27.0769V30.7692C21.3662 31.1138 20.5538 31.36 19.6923 31.5569V27.0769C18.3385 27.0769 17.2308 25.9692 17.2308 24.6154V16.7692H19.6923V22.1538H22.1539V16.7692H24.6154Z" fill="#9966FF"/>
    </svg>
  );
}
