/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        sand: "#f8f1e7",
        coral: "#f97316",
        moss: "#0f766e",
        gold: "#f59e0b",
      },
      boxShadow: {
        glow: "0 20px 60px rgba(15, 118, 110, 0.18)",
      },
    },
  },
  plugins: [],
};
