/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
theme: {
  extend: {
    colors: {
      tau: {
        primary: '#630f2c',
        hover: '#521025',
      },
    },
  },
},

  plugins: [],
}
