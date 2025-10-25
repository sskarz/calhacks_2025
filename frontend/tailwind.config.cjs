/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        platform: {
          ebay: "#3665f3",
          etsy: "#f1641e",
          shopify: "#95bf47"
        }
      }
    }
  },
  plugins: []
};
