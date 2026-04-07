async function test() {
    const r1 = await fetch('https://simhpc.com/');
    const html = await r1.text();
    const match = html.match(/\/assets\/index-[a-zA-Z0-9_-]+\.js/);
    if (!match) return console.log('not found');
    const r2 = await fetch('https://simhpc.com' + match[0]);
    const js = await r2.text();

    // Evaluate it in a very basic DOM mock
    const vm = require('vm');
    const sandbox = {
        window: {
            navigator: { userAgent: 'node' },
            location: { pathname: '/', search: '', hash: '', origin: 'https://simhpc.com' },
            performance: { now: () => 0 },
            addEventListener: () => { },
            removeEventListener: () => { },
            matchMedia: () => ({ matches: false, addListener: () => { }, removeListener: () => { } }),
            requestAnimationFrame: setTimeout,
            cancelAnimationFrame: clearTimeout,
        },
        document: {
            getElementById: () => {
                const node = {
                    appendChild: () => { }, children: [], append: () => { }, nodeType: 1,
                    hasChildNodes: () => false, setAttribute: () => { }, removeAttribute: () => { },
                    style: {}
                };
                return node;
            },
            querySelector: () => {
                return {
                    appendChild: () => { }, children: [], append: () => { }, nodeType: 1,
                    hasChildNodes: () => false, setAttribute: () => { }, removeAttribute: () => { },
                    style: {}
                };
            },
            querySelectorAll: () => [],
            getElementsByTagName: () => [],
            createElement: () => ({
                setAttribute: () => { }, style: {}, appendChild: () => { },
                className: '', classList: { add: () => { }, remove: () => { } }
            }),
            location: { href: 'https://simhpc.com', pathname: '/' },
            addEventListener: () => { },
            removeEventListener: () => { },
            createEvent: () => ({ initEvent: () => { } }),
            documentElement: { style: {} },
            body: { style: {}, appendChild: () => { }, removeChild: () => { } }
        },
        navigator: { userAgent: 'node' },
        self: null,
        globalThis: null,
        console: console,
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        setInterval: setInterval,
        clearInterval: clearInterval,
        MutationObserver: class { observe() { } disconnect() { } }
    };
    sandbox.self = sandbox.window;
    sandbox.globalThis = sandbox.window;
    sandbox.document.defaultView = sandbox.window;
    sandbox.window.document = sandbox.document;
    sandbox.window.window = sandbox.window;
    sandbox.window.localStorage = { getItem: () => null, setItem: () => { } };
    sandbox.localStorage = sandbox.window.localStorage;

    try {
        const script = new vm.Script(js);
        script.runInNewContext(sandbox);
        console.log('Script loaded perfectly');
    } catch (e) {
        console.log('EVAL ERROR:', e.message);
        console.log(e.stack);
    }
}
test();
