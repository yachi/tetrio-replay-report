// Minimal chalk stand-in: the vendored engine uses chalk ONLY for cosmetic terminal colour in a
// deprecation warning and a debug board-printer, neither on the simulation path. A Proxy whose every
// property is a chainable identity function reproduces `chalk.redBright(x)`, `chalk.bgHex('#f80')(x)`,
// etc. without pulling the 16 MB @haelp/teto client (chalk was its only external engine dependency).
const identity = (...args) => args.map(a => (typeof a === 'string' ? a : '')).join(' ');
const handler = {
  get: () => new Proxy(identity, handler),
  apply: (_t, _this, args) => (typeof args[0] === 'string' ? args[0] : new Proxy(identity, handler)),
};
export default new Proxy(identity, handler);
