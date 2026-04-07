const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
    page.on('response', response => {
        if (!response.ok()) {
            console.log('FAILED REQUEST:', response.url(), response.status());
        }
    });

    try {
        await page.goto('https://simhpc-frontend-msf44wacu-btwndlinezs-projects.vercel.app', { waitUntil: 'networkidle2' });
        console.log("Page loaded successfully.");
    } catch (e) {
        console.log("Navigation error:", e.message);
    }
    await browser.close();
})();
