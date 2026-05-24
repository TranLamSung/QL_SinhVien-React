import { useState, useEffect } from "react";

// Hook này nhận vào một giá trị và thời gian chờ (mặc định 500ms)
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Thiết lập đồng hồ đếm ngược
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 🌟 CHÌA KHÓA: Nếu người dùng gõ tiếp, hàm cleanup này sẽ chạy 
    // để XÓA ĐỒNG HỒ CŨ đi trước khi nó kịp chạy hết giờ!
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}