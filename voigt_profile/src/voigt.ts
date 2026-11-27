// Weideman's rational approximation (SIAM J. Numer. Anal. 31, 1994).
// Re[w(x + iy)] is the Gaussian–Lorentzian convolution up to a constant.
const order = 32;
const size = 4 * order;
const length = Math.sqrt(order / Math.SQRT2);
const grid = Array.from({ length: size }, (_, index) => {
  if (index === 0) return 0;
  const tangent = length * Math.tan(Math.PI * (index - size / 2) / size);
  return Math.exp(-tangent * tangent) * (length * length + tangent * tangent);
});
const coefficients = Array.from({ length: order }, (_, index) => {
  const frequency = order - index;
  return grid.reduce((sum, value, sample) =>
    sum + value * Math.cos(2 * Math.PI * frequency * (sample - size / 2) / size), 0) / size;
});

export function voigtReal(x: number, y: number): number {
  const d = length + y;
  const norm = d * d + x * x;
  const inverseReal = d / norm;
  const inverseImag = x / norm;
  // (L + iz) / (L - iz) = 2L / (L - iz) - 1.
  const zr = 2 * length * inverseReal - 1;
  const zi = 2 * length * inverseImag;
  let real = 0;
  let imag = 0;
  for (const coefficient of coefficients) {
    const next = real * zr - imag * zi + coefficient;
    imag = real * zi + imag * zr;
    real = next;
  }
  return 2 * (real * (inverseReal * inverseReal - inverseImag * inverseImag) -
    2 * imag * inverseReal * inverseImag) + inverseReal / Math.sqrt(Math.PI);
}
