const { scrypt, syncScrypt } = require('scrypt-js');

(function() {
    "use strict";
    var wn, dn = {
        exports: {}
    };
    wn = dn,
    function() {
        function n(s) {
            const r = new Uint32Array([1116352408, 1899447441, 3049323471, 3921009573, 961987163, 1508970993, 2453635748, 2870763221, 3624381080, 310598401, 607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580, 3835390401, 4022224774, 264347078, 604807628, 770255983, 1249150122, 1555081692, 1996064986, 2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711, 113926993, 338241895, 666307205, 773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037, 2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909, 275423344, 430227734, 506948616, 659060556, 883997877, 958139571, 1322822218, 1537002063, 1747873779, 1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298]);
            let o = 1779033703
              , a = 3144134277
              , f = 1013904242
              , l = 2773480762
              , c = 1359893119
              , b = 2600822924
              , v = 528734635
              , g = 1541459225;
            const N = new Uint32Array(64);
            function E(J) {
                let W = 0
                  , P = J.length;
                for (; P >= 64; ) {
                    let C, m, X, B, w, j = o, d = a, L = f, bn = l, U = c, Y = b, _ = v, gn = g;
                    for (m = 0; m < 16; m++)
                        X = W + 4 * m,
                        N[m] = (255 & J[X]) << 24 | (255 & J[X + 1]) << 16 | (255 & J[X + 2]) << 8 | 255 & J[X + 3];
                    for (m = 16; m < 64; m++)
                        C = N[m - 2],
                        B = (C >>> 17 | C << 15) ^ (C >>> 19 | C << 13) ^ C >>> 10,
                        C = N[m - 15],
                        w = (C >>> 7 | C << 25) ^ (C >>> 18 | C << 14) ^ C >>> 3,
                        N[m] = (B + N[m - 7] | 0) + (w + N[m - 16] | 0) | 0;
                    for (m = 0; m < 64; m++)
                        B = (((U >>> 6 | U << 26) ^ (U >>> 11 | U << 21) ^ (U >>> 25 | U << 7)) + (U & Y ^ ~U & _) | 0) + (gn + (r[m] + N[m] | 0) | 0) | 0,
                        w = ((j >>> 2 | j << 30) ^ (j >>> 13 | j << 19) ^ (j >>> 22 | j << 10)) + (j & d ^ j & L ^ d & L) | 0,
                        gn = _,
                        _ = Y,
                        Y = U,
                        U = bn + B | 0,
                        bn = L,
                        L = d,
                        d = j,
                        j = B + w | 0;
                    o = o + j | 0,
                    a = a + d | 0,
                    f = f + L | 0,
                    l = l + bn | 0,
                    c = c + U | 0,
                    b = b + Y | 0,
                    v = v + _ | 0,
                    g = g + gn | 0,
                    W += 64,
                    P -= 64
                }
            }
            E(s);
            let z, q = s.length % 64, G = s.length / 536870912 | 0, M = s.length << 3, V = q < 56 ? 56 : 120, S = s.slice(s.length - q, s.length);
            for (S.push(128),
            z = q + 1; z < V; z++)
                S.push(0);
            return S.push(G >>> 24 & 255),
            S.push(G >>> 16 & 255),
            S.push(G >>> 8 & 255),
            S.push(G >>> 0 & 255),
            S.push(M >>> 24 & 255),
            S.push(M >>> 16 & 255),
            S.push(M >>> 8 & 255),
            S.push(M >>> 0 & 255),
            E(S),
            [o >>> 24 & 255, o >>> 16 & 255, o >>> 8 & 255, o >>> 0 & 255, a >>> 24 & 255, a >>> 16 & 255, a >>> 8 & 255, a >>> 0 & 255, f >>> 24 & 255, f >>> 16 & 255, f >>> 8 & 255, f >>> 0 & 255, l >>> 24 & 255, l >>> 16 & 255, l >>> 8 & 255, l >>> 0 & 255, c >>> 24 & 255, c >>> 16 & 255, c >>> 8 & 255, c >>> 0 & 255, b >>> 24 & 255, b >>> 16 & 255, b >>> 8 & 255, b >>> 0 & 255, v >>> 24 & 255, v >>> 16 & 255, v >>> 8 & 255, v >>> 0 & 255, g >>> 24 & 255, g >>> 16 & 255, g >>> 8 & 255, g >>> 0 & 255]
        }
        function t(s, r, o) {
            s = s.length <= 64 ? s : n(s);
            const a = 64 + r.length + 4
              , f = new Array(a)
              , l = new Array(64);
            let c, b = [];
            for (c = 0; c < 64; c++)
                f[c] = 54;
            for (c = 0; c < s.length; c++)
                f[c] ^= s[c];
            for (c = 0; c < r.length; c++)
                f[64 + c] = r[c];
            for (c = a - 4; c < a; c++)
                f[c] = 0;
            for (c = 0; c < 64; c++)
                l[c] = 92;
            for (c = 0; c < s.length; c++)
                l[c] ^= s[c];
            function v() {
                for (let g = a - 1; g >= a - 4; g--) {
                    if (f[g]++,
                    f[g] <= 255)
                        return;
                    f[g] = 0
                }
            }
            for (; o >= 32; )
                v(),
                b = b.concat(n(l.concat(n(f)))),
                o -= 32;
            return o > 0 && (v(),
            b = b.concat(n(l.concat(n(f))).slice(0, o))),
            b
        }
        function i(s, r, o, a, f) {
            let l;
            for (p(s, 16 * (2 * o - 1), f, 0, 16),
            l = 0; l < 2 * o; l++)
                I(s, 16 * l, f, 16),
                h(f, a),
                p(f, 0, s, r + 16 * l, 16);
            for (l = 0; l < o; l++)
                p(s, r + 2 * l * 16, s, 16 * l, 16);
            for (l = 0; l < o; l++)
                p(s, r + 16 * (2 * l + 1), s, 16 * (l + o), 16)
        }
        function u(s, r) {
            return s << r | s >>> 32 - r
        }
        function h(s, r) {
            p(s, 0, r, 0, 16);
            for (let o = 8; o > 0; o -= 2)
                r[4] ^= u(r[0] + r[12], 7),
                r[8] ^= u(r[4] + r[0], 9),
                r[12] ^= u(r[8] + r[4], 13),
                r[0] ^= u(r[12] + r[8], 18),
                r[9] ^= u(r[5] + r[1], 7),
                r[13] ^= u(r[9] + r[5], 9),
                r[1] ^= u(r[13] + r[9], 13),
                r[5] ^= u(r[1] + r[13], 18),
                r[14] ^= u(r[10] + r[6], 7),
                r[2] ^= u(r[14] + r[10], 9),
                r[6] ^= u(r[2] + r[14], 13),
                r[10] ^= u(r[6] + r[2], 18),
                r[3] ^= u(r[15] + r[11], 7),
                r[7] ^= u(r[3] + r[15], 9),
                r[11] ^= u(r[7] + r[3], 13),
                r[15] ^= u(r[11] + r[7], 18),
                r[1] ^= u(r[0] + r[3], 7),
                r[2] ^= u(r[1] + r[0], 9),
                r[3] ^= u(r[2] + r[1], 13),
                r[0] ^= u(r[3] + r[2], 18),
                r[6] ^= u(r[5] + r[4], 7),
                r[7] ^= u(r[6] + r[5], 9),
                r[4] ^= u(r[7] + r[6], 13),
                r[5] ^= u(r[4] + r[7], 18),
                r[11] ^= u(r[10] + r[9], 7),
                r[8] ^= u(r[11] + r[10], 9),
                r[9] ^= u(r[8] + r[11], 13),
                r[10] ^= u(r[9] + r[8], 18),
                r[12] ^= u(r[15] + r[14], 7),
                r[13] ^= u(r[12] + r[15], 9),
                r[14] ^= u(r[13] + r[12], 13),
                r[15] ^= u(r[14] + r[13], 18);
            for (let o = 0; o < 16; ++o)
                s[o] += r[o]
        }
        function I(s, r, o, a) {
            for (let f = 0; f < a; f++)
                o[f] ^= s[r + f]
        }
        function p(s, r, o, a, f) {
            for (; f--; )
                o[a++] = s[r++]
        }
        function k(s) {
            if (!s || typeof s.length != "number")
                return !1;
            for (let r = 0; r < s.length; r++) {
                const o = s[r];
                if (typeof o != "number" || o % 1 || o < 0 || o >= 256)
                    return !1
            }
            return !0
        }
        function y(s, r) {
            if (typeof s != "number" || s % 1)
                throw new Error("invalid " + r);
            return s
        }
        function A(s, r, o, a, f, l, c) {
            if (o = y(o, "N"),
            a = y(a, "r"),
            f = y(f, "p"),
            l = y(l, "dkLen"),
            o === 0 || o & o - 1)
                throw new Error("N must be power of 2");
            if (o > 2147483647 / 128 / a)
                throw new Error("N too large");
            if (a > 2147483647 / 128 / f)
                throw new Error("r too large");
            if (!k(s))
                throw new Error("password must be an array or buffer");
            if (s = Array.prototype.slice.call(s),
            !k(r))
                throw new Error("salt must be an array or buffer");
            r = Array.prototype.slice.call(r);
            let b = t(s, r, 128 * f * a);
            const v = new Uint32Array(32 * f * a);
            for (let w = 0; w < v.length; w++) {
                const j = 4 * w;
                v[w] = (255 & b[j + 3]) << 24 | (255 & b[j + 2]) << 16 | (255 & b[j + 1]) << 8 | 255 & b[j + 0]
            }
            const g = new Uint32Array(64 * a)
              , N = new Uint32Array(32 * a * o)
              , E = 32 * a
              , z = new Uint32Array(16)
              , q = new Uint32Array(16)
              , G = f * o * 2;
            let M, V, S = 0, J = null, W = !1, P = 0, C = 0;
            const m = c ? parseInt(1e3 / a) : 4294967295
              , X = typeof setImmediate < "u" ? setImmediate : setTimeout
              , B = function() {
                if (W)
                    return c(new Error("cancelled"), S / G);
                let w;
                switch (P) {
                case 0:
                    V = 32 * C * a,
                    p(v, V, g, 0, E),
                    P = 1,
                    M = 0;
                case 1:
                    w = o - M,
                    w > m && (w = m);
                    for (let d = 0; d < w; d++)
                        p(g, 0, N, (M + d) * E, E),
                        i(g, E, a, z, q);
                    if (M += w,
                    S += w,
                    c) {
                        const d = parseInt(1e3 * S / G);
                        if (d !== J) {
                            if (W = c(null, S / G),
                            W)
                                break;
                            J = d
                        }
                    }
                    if (M < o)
                        break;
                    M = 0,
                    P = 2;
                case 2:
                    w = o - M,
                    w > m && (w = m);
                    for (let d = 0; d < w; d++) {
                        const L = g[16 * (2 * a - 1)] & o - 1;
                        I(N, L * E, g, E),
                        i(g, E, a, z, q)
                    }
                    if (M += w,
                    S += w,
                    c) {
                        const d = parseInt(1e3 * S / G);
                        if (d !== J) {
                            if (W = c(null, S / G),
                            W)
                                break;
                            J = d
                        }
                    }
                    if (M < o)
                        break;
                    if (p(g, 0, v, V, E),
                    C++,
                    C < f) {
                        P = 0;
                        break
                    }
                    b = [];
                    for (let d = 0; d < v.length; d++)
                        b.push(255 & v[d]),
                        b.push(v[d] >> 8 & 255),
                        b.push(v[d] >> 16 & 255),
                        b.push(v[d] >> 24 & 255);
                    const j = t(s, b, l);
                    return c && c(null, 1, j),
                    j
                }
                c && X(B)
            };
            if (!c)
                for (; ; ) {
                    const w = B();
                    if (w != null)
                        return w
                }
            B()
        }
        const K = {
            scrypt: function(s, r, o, a, f, l, c) {
                return new Promise(function(b, v) {
                    let g = 0;
                    c && c(0),
                    A(s, r, o, a, f, l, function(N, E, z) {
                        if (N)
                            v(N);
                        else if (z)
                            c && g !== 1 && c(1),
                            b(new Uint8Array(z));
                        else if (c && E !== g)
                            return g = E,
                            c(E)
                    })
                }
                )
            },
            syncScrypt: function(s, r, o, a, f, l) {
                return new Uint8Array(A(s, r, o, a, f, l))
            }
        };
        wn.exports = K
    }();
    var jn = dn.exports;
    function Q(e, n) {
        const t = Z();
        return (Q = function(i, u) {
            return t[i -= 188]
        }
        )(e, n)
    }
    (function(e) {
        const n = Q
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(204)) / 1 * (-parseInt(n(191)) / 2) + parseInt(n(190)) / 3 * (-parseInt(n(211)) / 4) + parseInt(n(205)) / 5 * (parseInt(n(195)) / 6) + -parseInt(n(194)) / 7 * (parseInt(n(208)) / 8) + -parseInt(n(214)) / 9 * (-parseInt(n(202)) / 10) + -parseInt(n(200)) / 11 * (-parseInt(n(206)) / 12) + parseInt(n(188)) / 13 * (parseInt(n(189)) / 14) === 402028)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }
    )(Z);
    function Z() {
        const e = ["slice", "48937uMtdFw", "17994zZmGBM", "toString", "map", "iCPkY", "zNjaF", "7883843EiJgSa", "push", "10DUEJcc", "getSeconds", "145JGZLbc", "235MKqbJF", "12EUqhQZ", "charCodeAt", "408uBTSAl", "value", "length", "207864CrXQUf", "now", "answers_count", "990153jOWPbf", "FjcrK", "buffer_len", "tvnCP", "split", "normalize", "reverse", "13bJjlos", "4250526gpukpX", "39frVNxb", "2246NzSvZh", "CGJth"];
        return (Z = function() {
            return e
        }
        )()
    }
    const xn = e => {
        const n = Q
          , t = {
            CGJth: function(h, I) {
                return h + I
            }
        }
          , i = t;
        let u = 0;
        for (let h = e[n(210)] - 1; h >= 0; h -= 1)
            u = i[n(192)](256 * u, e[h]);
        return u
    }
      , mn = e => {
        const n = Q;
        return Uint8Array.from(e[n(219)]("NFKC")[n(218)]("")[n(197)](t => t[n(207)](0)))
    }
      , Cn = e => {
        const n = Q
          , t = {};
        t[n(198)] = function(K, s) {
            return K + s
        }
        ,
        t[n(217)] = function(K, s) {
            return K < s
        }
        ,
        t[n(199)] = function(K, s) {
            return K > s
        }
        ;
        const i = t
          , u = mn(e[n(209)])
          , h = parseInt(e.threshold_hex, 16)
          , I = [];
        let p = 0;
        const k = (K => {
            const s = Q;
            let r = 3;
            const {value: o} = K
              , a = o[s(193)](-2);
            return r = {
                FjcrK: function(f, l, c) {
                    return f(l, c)
                }
            }[s(215)](parseInt, a, 16),
            r
        }
        )(e)
          , y = new Date
          , A = y.setSeconds(i[n(198)](y[n(203)](), k));
        for (; I.length < e[n(213)] || i.tvnCP(Date[n(212)](), A); ) {
            for (; i[n(199)](xn(jn.syncScrypt(u, mn(p[n(196)]()), e.n, e.r, 1, e[n(216)])[n(220)]()), h); )
                p += 1;
            I[n(201)](p),
            p += 1
        }
        return {
            task: e,
            answers: I[n(193)](0, e.answers_count)
        }
    }
      , D = {
        name: "challenge_pow",
        private: !0,
        version: "1.0.1",
        type: "module",
        description: "Headless browser and fingerprint functionality",
        license: "ISC",
        repository: {
            type: "git",
            url: "git@gitlab-private.wildberries.ru:antiddos/antibot/challenge-pow.git"
        },
        files: ["dist"],
        scripts: {
            dev: "vite",
            build: "tsc && vite build",
            preview: "vite preview"
        },
        dependencies: {
            "scrypt-js": "^3.0.1"
        },
        devDependencies: {
            "@babel/core": "^7.24.5",
            "@babel/plugin-transform-nullish-coalescing-operator": "^7.24.7",
            "@babel/plugin-transform-runtime": "^7.21.4",
            "@babel/preset-env": "^7.21.5",
            "@babel/preset-typescript": "^7.21.5",
            "@rollup/plugin-babel": "^6.0.4",
            "@rollup/plugin-terser": "^0.4.4",
            "@types/node": "^22.10.0",
            "@typescript-eslint/eslint-plugin": "^5.59.2",
            "@typescript-eslint/parser": "^5.59.2",
            eslint: "^8.39.0",
            "eslint-config-airbnb": "^19.0.4",
            "eslint-config-prettier": "^8.8.0",
            "eslint-import-resolver-typescript": "^3.5.5",
            "eslint-plugin-import": "^2.27.5",
            "eslint-plugin-prettier": "^4.2.1",
            "eslint-plugin-unused-imports": "^2.0.0",
            prettier: "^2.8.8",
            "rollup-obfuscator": "^4.1.1",
            typescript: "~5.6.2",
            vite: "^5.4.10",
            "vite-plugin-commonjs": "^0.10.4",
            "vite-tsconfig-paths": "^5.1.3"
        }
    };
    function R() {
        const e = ["455758IfsEdG", "1666506BlKgry", "name", "version", "398759kmQAjJ", "645QXPmOd", "3454682HTzpKc", "100593uIeALT", "1528gTfsHO", "5284GnZBny", "1532739tiIlko"];
        return (R = function() {
            return e
        }
        )()
    }
    function $(e, n) {
        const t = R();
        return ($ = function(i, u) {
            return t[i -= 238]
        }
        )(e, n)
    }
    function nn(e, n) {
        const t = rn();
        return (nn = function(i, u) {
            return t[i -= 497]
        }
        )(e, n)
    }
    function rn() {
        const e = ["6ISllbj", "charCodeAt", "GOqwL", "abs", "131976vjYoXy", "hbItv", "1342676SkitGF", "length", "2034060Hwboef", "510944QwsFuc", "2699284DgKZCp", "7208720aisFVX", "2692415HcFuJL"];
        return (rn = function() {
            return e
        }
        )()
    }
    function tn() {
        const e = ["22GuuiAa", "552645RfxdnA", "30pQBWvm", "690pGMwvj", "zIuYn", "1495144MPRrsj", "4492rsJgEe", "56Axyxlt", "1386387FWEOFw", "190ypBubO", "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "4024IjNhCX", "8635224tUVrGA", "floor", "2821gOkncf", "length", "charAt"];
        return (tn = function() {
            return e
        }
        )()
    }
    function en(e, n) {
        const t = tn();
        return (en = function(i, u) {
            return t[i -= 327]
        }
        )(e, n)
    }
    function sn(e, n) {
        const t = on();
        return (sn = function(i, u) {
            return t[i -= 351]
        }
        )(e, n)
    }
    function on() {
        const e = ["5227187VORVGS", "35nXUQgP", "KnNMf", "74080PtlyrD", "encode", "845445KrQZws", "20xaezAK", "11076318RTKOMM", "1388953tZhzfy", "40rqMora", "9831824MpUPbD", "517008VlMkKg"];
        return (on = function() {
            return e
        }
        )()
    }
    (function(e) {
        const n = $
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(248)) / 1 + -parseInt(n(244)) / 2 + -parseInt(n(243)) / 3 + -parseInt(n(242)) / 4 * (-parseInt(n(238)) / 5) + -parseInt(n(245)) / 6 + -parseInt(n(239)) / 7 + parseInt(n(241)) / 8 * (parseInt(n(240)) / 9) === 396388)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }
    )(R),
    function(e) {
        const n = nn
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(504)) / 1 + parseInt(n(499)) / 2 + -parseInt(n(503)) / 3 + -parseInt(n(501)) / 4 + parseInt(n(507)) / 5 * (parseInt(n(508)) / 6) + parseInt(n(505)) / 7 + parseInt(n(506)) / 8 === 366540)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }(rn),
    function(e) {
        const n = en
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(334)) / 1 * (parseInt(n(335)) / 2) + parseInt(n(329)) / 3 + -parseInt(n(333)) / 4 + -parseInt(n(337)) / 5 * (-parseInt(n(331)) / 6) + -parseInt(n(342)) / 7 * (parseInt(n(339)) / 8) + -parseInt(n(336)) / 9 * (parseInt(n(330)) / 10) + parseInt(n(328)) / 11 * (parseInt(n(340)) / 12) === 463389)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }(tn),
    function(e) {
        const n = sn
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(360)) / 1 + parseInt(n(355)) / 2 + parseInt(n(357)) / 3 * (-parseInt(n(358)) / 4) + -parseInt(n(353)) / 5 * (-parseInt(n(351)) / 6) + -parseInt(n(352)) / 7 + -parseInt(n(362)) / 8 + -parseInt(n(359)) / 9 * (-parseInt(n(361)) / 10) === 789277)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }(on);
    const x = un;
    function un(e, n) {
        const t = cn();
        return (un = function(i, u) {
            return t[i -= 456]
        }
        )(e, n)
    }
    (function(e) {
        const n = un
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(466)) / 1 * (-parseInt(n(462)) / 2) + parseInt(n(468)) / 3 * (parseInt(n(465)) / 4) + parseInt(n(474)) / 5 + parseInt(n(477)) / 6 * (parseInt(n(471)) / 7) + -parseInt(n(459)) / 8 + -parseInt(n(464)) / 9 * (-parseInt(n(470)) / 10) + -parseInt(n(458)) / 11 === 603856)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }
    )(cn);
    const F = {};
    function cn() {
        const e = ["value", "goamk", "3692yfJqBq", "vcCVf", "153RnfTuT", "352204dAJSin", "335JXaCSr", "number", "6rlqCCL", "entries", "272660wjqGck", "86093zWiZlV", "every", "answers_count", "1760795jOvSdC", "siteKey", "buffer_len", "588qosRAs", "deviceToken", "timestamp", "string", "18669277snhQdi", "4115456kWyZYj"];
        return (cn = function() {
            return e
        }
        )()
    }
    F[x(473)] = "number",
    F[x(476)] = x(467),
    F.n = x(467),
    F.r = x(467),
    F.threshold_hex = x(457),
    F[x(456)] = x(467),
    F[x(460)] = x(457);
    const O = {
        ...F
    };
    O.version = "number",
    O.id = x(457),
    O.ip = x(457),
    O.ua = x(457),
    O[x(475)] = "string",
    O[x(478)] = x(457);
    const En = O;
    function Kn(e, n) {
        const t = x
          , i = {};
        i[t(463)] = function(I, p) {
            return I !== p
        }
        ,
        i[t(461)] = function(I, p) {
            return I === p
        }
        ;
        const u = i;
        let h = !0;
        return Object[t(469)](n)[t(472)](I => {
            const p = t;
            let[k,y] = I;
            const A = e[k];
            return !(!u.vcCVf(A, void 0) || !u[p(461)](typeof A, y)) || (h = !1,
            !1)
        }
        ),
        h
    }
    function H(e, n) {
        const t = an();
        return (H = function(i, u) {
            return t[i -= 451]
        }
        )(e, n)
    }
    function an() {
        const e = ["5733xdNiDH", "nWnEG", "length", "encode", "fromCharCode", "5182446JmlQyX", "10677360WKsYoz", "push", "70570GkmESZ", "XKbUd", "ApNSw", "toString", "dEzbU", "367156smPsnj", "apply", "4687074nmXCxQ", "63740BsfxKX", "75oPmnNl", "2XnuiWs", "string", "split", "12832472TSMnam", "nuCHk", "LBZWM"];
        return (an = function() {
            return e
        }
        )()
    }
    function Mn(e, n) {
        const t = H
          , i = {};
        i[t(468)] = function(p, k) {
            return p < k
        }
        ;
        const u = i
          , h = []
          , I = function(p, k) {
            const y = H
              , A = {
                dEzbU: y(464),
                nuCHk: function(o, a) {
                    return o(a)
                },
                ApNSw: function(o, a) {
                    return o < a
                },
                nWnEG: function(o, a) {
                    return o % a
                }
            }
              , K = typeof p == A[y(457)]
              , s = K ? vn(p) : p
              , r = A[y(467)](vn, k);
            for (let o = 0; A[y(455)](o, s[y(471)]); o++)
                s[o] = s[o] ^ r[A[y(470)](o, r[y(471)])];
            return K ? s : String[y(473)][y(459)](String, s)
        }(e, n);
        for (let p = 0; u[t(468)](p, I[t(471)]); p++)
            h[t(452)](I[p][t(456)](16));
        return h.join(",")
    }
    function vn(e) {
        const n = H;
        return [...new TextEncoder()[n(472)](e)]
    }
    function fn() {
        var e = ["2485217uKjZbW", "10801952GhBzhJ", "14308020KhGhjv", "1KneOuH", "3BzSFkY", "13495BYXunH", "3414OmdmvY", "4163384eKxVzC", "9383kYqWxo", "710jaaTcA", "260818QWVYKB"];
        return (fn = function() {
            return e
        }
        )()
    }
    function kn(e, n) {
        var t = fn();
        return (kn = function(i, u) {
            return t[i -= 207]
        }
        )(e, n)
    }
    function pn(e, n) {
        const t = ln();
        return (pn = function(i, u) {
            return t[i -= 261]
        }
        )(e, n)
    }
    function Nn(e) {
        const n = pn
          , t = {
            gQYFB: function(k, y) {
                return k(y)
            },
            fbVMk: function(k, y, A) {
                return k(y, A)
            },
            Mriks: n(263)
        }
          , i = e[n(272)](1)
          , u = t.gQYFB(atob, i)
          , [,h] = u[n(274)](".")
          , I = atob(h)
          , p = JSON[n(265)](I);
        if (t[n(269)](Kn, p, En))
            return p;
        throw new Error(t.Mriks)
    }
    function ln() {
        const e = ["2994296hjIjnR", "1432942RYGyrM", "slice", "969995NnIthh", "split", "759609NyPHvX", "4SBLzVD", "Payload type is incorrect", "1284297NAszco", "parse", "13028598ecCLSa", "21RToQDK", "30042uodTAS", "fbVMk"];
        return (ln = function() {
            return e
        }
        )()
    }
    (function(e) {
        const n = H
          , t = e();
        for (; ; )
            try {
                if (parseInt(n(461)) / 1 * (parseInt(n(463)) / 2) + -parseInt(n(474)) / 3 + -parseInt(n(458)) / 4 * (parseInt(n(462)) / 5) + parseInt(n(451)) / 6 + -parseInt(n(460)) / 7 + -parseInt(n(466)) / 8 + -parseInt(n(469)) / 9 * (-parseInt(n(453)) / 10) === 960651)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }
    )(an),
    function(e) {
        for (var n = kn, t = e(); ; )
            try {
                if (parseInt(n(215)) / 1 * (-parseInt(n(211)) / 2) + -parseInt(n(216)) / 3 * (parseInt(n(208)) / 4) + parseInt(n(217)) / 5 * (parseInt(n(207)) / 6) + parseInt(n(212)) / 7 + -parseInt(n(213)) / 8 + parseInt(n(214)) / 9 + -parseInt(n(210)) / 10 * (parseInt(n(209)) / 11) === 898480)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }(fn),
    function(e) {
        const n = pn
          , t = e();
        for (; ; )
            try {
                if (parseInt(n(261)) / 1 + -parseInt(n(271)) / 2 + -parseInt(n(264)) / 3 + parseInt(n(262)) / 4 * (-parseInt(n(273)) / 5) + -parseInt(n(268)) / 6 * (parseInt(n(267)) / 7) + -parseInt(n(270)) / 8 + parseInt(n(266)) / 9 === 479354)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }(ln);
    const T = hn;
    function hn(e, n) {
        const t = In();
        return (hn = function(i, u) {
            return t[i -= 443]
        }
        )(e, n)
    }
    (function(e) {
        const n = hn
          , t = e();
        for (; ; )
            try {
                if (-parseInt(n(457)) / 1 * (parseInt(n(464)) / 2) + -parseInt(n(446)) / 3 * (parseInt(n(449)) / 4) + parseInt(n(444)) / 5 + parseInt(n(456)) / 6 * (-parseInt(n(452)) / 7) + parseInt(n(447)) / 8 * (-parseInt(n(462)) / 9) + -parseInt(n(460)) / 10 + -parseInt(n(448)) / 11 * (-parseInt(n(466)) / 12) === 762243)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }
    )(In);
    const Un = function(e) {
        const n = nn
          , t = {};
        t[n(500)] = function(h, I) {
            return h < I
        }
        ,
        t[n(497)] = function(h, I) {
            return h << I
        }
        ;
        const i = t;
        let u = 0;
        for (let h = 0, I = e[n(502)]; i[n(500)](h, I); h++) {
            let p = e[n(509)](h);
            u = i[n(497)](u, 5) - u + p,
            u |= 0
        }
        return String(Math[n(498)](u))
    }(function() {
        const e = $;
        return D[e(246)] + "_v" + (D[e(247)][0] === "0" ? 1 : D[e(247)])
    }())
      , An = Symbol[T(465)](Un);
    class Gn {
        constructor() {
            const n = T;
            this[n(453)] = this[n(453)][n(455)](this),
            this[n(458)]()
        }
        [T(458)]() {
            const n = T;
            !window[An] && (window[An] = this[n(453)])
        }
        async[T(453)](n) {
            const t = T
              , i = {
                Equye: function(a, f) {
                    return a(f)
                }
            }[t(461)](Nn, n)
              , {answers_count: u, buffer_len: h, n: I, r: p, sign: k, threshold_hex: y, timestamp: A, value: K, id: s} = i
              , r = {};
            r.answers_count = u,
            r[t(459)] = h,
            r.n = I,
            r.r = p,
            r[t(454)] = k,
            r[t(463)] = y,
            r[t(445)] = A,
            r[t(450)] = K;
            const o = Cn(r);
            return this.transform(o, s)
        }
        [T(451)](n, t) {
            const i = Mn(JSON[T(443)](n), t);
            return function(u) {
                const h = en
                  , I = {};
                I[h(332)] = h(338);
                let p = "";
                const k = I[h(332)]
                  , y = k[h(343)];
                let A = 0;
                for (; A < u; )
                    p += k[h(327)](Math[h(341)](Math.random() * y)),
                    A += 1;
                return p
            }(1) + function(u) {
                const h = sn
                  , I = new TextEncoder()[h(356)](u)
                  , p = String.fromCodePoint(...I);
                return {
                    KnNMf: function(k, y) {
                        return k(y)
                    }
                }[h(354)](btoa, p)
            }(i)
        }
    }
    function In() {
        const e = ["value", "transform", "2107Duyeft", "executeTask", "sign", "bind", "1332TWPywE", "30482kPjFUL", "initApi", "buffer_len", "11976020LherGr", "Equye", "62289xvWFrE", "threshold_hex", "58sAuwYL", "for", "480900cyslHk", "stringify", "4594275onXAes", "timestamp", "45WnpVwi", "1040nvsWrj", "825pnBxHk", "30428QwmuJS"];
        return (In = function() {
            return e
        }
        )()
    }
    function yn() {
        var e = ["178oLxxts", "6813dNytOE", "1959xeHisM", "119604FNUIix", "4993786yWdryu", "934782BNnUqt", "5117370kNqDzL", "15OhyGyL", "5464TjLqvi", "1659372XJHgSx"];
        return (yn = function() {
            return e
        }
        )()
    }
    function Sn(e, n) {
        var t = yn();
        return (Sn = function(i, u) {
            return t[i -= 359]
        }
        )(e, n)
    }
    new Gn,
    function(e) {
        for (var n = Sn, t = e(); ; )
            try {
                if (-parseInt(n(365)) / 1 * (-parseInt(n(363)) / 2) + -parseInt(n(368)) / 3 + -parseInt(n(366)) / 4 * (parseInt(n(360)) / 5) + parseInt(n(362)) / 6 + -parseInt(n(367)) / 7 + parseInt(n(361)) / 8 * (parseInt(n(364)) / 9) + parseInt(n(359)) / 10 === 364986)
                    break;
                t.push(t.shift())
            } catch {
                t.push(t.shift())
            }
    }(yn)
}
)();
