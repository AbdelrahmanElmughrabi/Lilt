// pywebview's default API builder uses new Function, which strict CSP blocks.
// Keep its native transport and callbacks, but build methods with closures.
window.pywebview._createApi = function (functions) {
  const bridge = window.pywebview;
  for (const { func } of functions) {
    const hierarchy = func.split('.');
    const name = hierarchy.pop();
    const target = hierarchy.reduce((object, part) => object[part] ||= {}, bridge.api);
    bridge._returnValuesCallbacks[func] ||= {};
    target[name] = function (...args) {
      const id = crypto.randomUUID().replaceAll('-', '');
      return new Promise((resolve, reject) => {
        bridge._checkValue(func, resolve, reject, id);
        try {
          bridge._jsApiCallback(func, args, id);
        } catch (error) {
          delete bridge._returnValuesCallbacks[func][id];
          reject(error);
        }
      });
    };
  }
};
