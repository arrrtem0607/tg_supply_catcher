// starter.js
import { JSDOM } from 'jsdom';
import fs from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url'; // <--- этого у тебя не хватает
import path from 'path';




const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);


// Эмуляция браузерного окружения
const dom = new JSDOM('<html><head></head><body></body></html>', {
    runScripts: 'dangerously',
    resources: 'usable'
});
const window = dom.window;
global.window = window;
global.document = window.document;
import scryptPkg from 'scrypt-js';
const { scrypt, syncScrypt } = scryptPkg;


// до загрузки скрипта
global.window.require = (moduleName) => {
    if (moduleName === 'scrypt-js') {
        return { scrypt, syncScrypt };
    }
    throw new Error(`Cannot require module ${moduleName}`);
};

import { TextEncoder, TextDecoder } from 'util';

global.window.TextEncoder = TextEncoder;
global.window.TextDecoder = TextDecoder;

// Переопределение функции Symbol.for (если требуется)
const originalSymbolFor = window.Symbol.for;
window.Symbol.for = (key) => {
    return originalSymbolFor.call(window.Symbol, key);
};

// Исходный код функции F (starter.js)
var S = /^.*\/(.*)\.js/i;
        async function F(e) {
            const {scriptPath: t, payload: r} = e
              , s = function(e) {
                const t = function(e) {
                    const t = e.match(S);
                    if (t)
                        return t[1];
                    throw new Error(`Cannot match filename from script: ${e}`)
                }(e)
                  , r = (e => {
                    let t = 0;
                    for (let r = 0, s = e.length; r < s; r++)
                        t = (t << 5) - t + e.charCodeAt(r),
                        t |= 0;
                    return String(Math.abs(t))
                }
                )(t);
                return window.Symbol.for(r)
            }(t)
              , i = await (e => new Promise(( (t, r) => {
                const s = window.document.createElement("script");
                s.src = e,
                s.async = !0,
                s.type = "text/javascript";
                try {
                    window.document.getElementsByTagName("head")[0].appendChild(s)
                } catch {
                    window.document.body.append(s)
                }

                    t(!0)

                s.addEventListener("error", (e => {
                    r(e)
                }
                ))
            }
            )))(t)
              , n = await (async e => (e => {
                const {attempts: t, interval: r, isLoadedCallback: s} = e;
                return new Promise(( (e, i) => {
                    let n = 0
                      , o = window.setInterval(( () => {
                        n += 1;
                        const r = s();
                        (r || n === t) && (window.clearInterval(o),
                        o = null,
                        r ? e(!0) : i(new Error("checkApiAttempts error")))
                    }
                    ), r)
                }
                ))
            }
            )({
                attempts: 3,
                interval: 500,
                isLoadedCallback: () => (e => "function" == typeof window[e])(e)
            }))(s);
            if (i && n)
                return await window[s](r);
            throw new Error(`Error while solving challenge by url: ${t}`)
        }

// Загрузка скрипта challenge_pow_v1.0.1.js локально
async function loadScript(scriptPath) {
    const scriptContent = fs.readFileSync(path.join(__dirname, 'scripts', 'challenge_pow_v1.0.1.js'), 'utf-8');
    window.eval(scriptContent); // Исполнение скрипта в эмулированном окружении
}
// Запуск функции F
(async () => {
    try {
        const scriptPath = '/scripts/challenge_pow_v1.0.1.js';


        await loadScript(path.join(__dirname, 'scripts', 'challenge_pow_v1.0.1.js'));        const args = process.argv.slice(2);
        const payload = args[0]
        const result = await F({
            scriptPath: scriptPath,
            payload: payload
        });

        process.stdout.write(result);

    } catch (error) {
        console.error('Ошибка:', error);
    }
})();