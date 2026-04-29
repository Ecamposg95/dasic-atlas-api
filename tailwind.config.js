/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
      },
      colors: {
        dasic: {
          navy: "#001e62",
          cyan: "#00d4e0",
        },
        sidebar: {
          bg: "#0a1429",
          "bg-bottom": "#050a1a",
          accent: "#00d4e0",
        },
      },
    },
  },
  plugins: [],
};
