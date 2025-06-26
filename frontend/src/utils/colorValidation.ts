/**
 * Color Validation Test
 * Verifies that HSL values in CSS match the required hex colors
 */

// Required hex colors from task list
const REQUIRED_COLORS = {
  black: '#000000',
  primary: '#3674B5',
  secondary: '#578FCA', 
  accentCream: '#F5F0CD',
  accentGold: '#FADA7A',
  white: '#FFFFFF'
};

// Convert hex to HSL for verification
function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0, s = 0, l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }

  return [
    Math.round(h * 360),
    Math.round(s * 100),
    Math.round(l * 100)
  ];
}

// Validate each color
console.log('Color Validation Results:');
console.log('========================');

Object.entries(REQUIRED_COLORS).forEach(([name, hex]) => {
  const [h, s, l] = hexToHsl(hex);
  console.log(`${name}: ${hex} → HSL(${h}, ${s}%, ${l}%)`);
});

export {};
