module.exports = {
    content: [
        "./templates/**/*.html",
        "./templates/*.html",
        "./static/js/**/*.js"
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                sidebar: {
                    DEFAULT: "#1e293b",
                    dark: "#0f172a",
                    hover: "#334155"
                }
            }
        }
    },
    plugins: []
};
