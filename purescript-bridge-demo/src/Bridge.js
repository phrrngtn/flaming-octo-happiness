// FFI for Bridge.purs — CustomEvent dispatch/listen

export const dispatchPsEvent = function (json) {
  return function () {
    document.dispatchEvent(
      new CustomEvent("__ps_event__", { detail: json })
    );
  };
};

export const subscribeQtCommands = function (callback) {
  return function () {
    var handler = function (e) {
      callback(e.detail)();
    };
    document.addEventListener("__qt_command__", handler);
    // Return unsubscribe effect
    return function () {
      document.removeEventListener("__qt_command__", handler);
    };
  };
};
