import{createRequire}from'node:module';const require=createRequire(import.meta.url);
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
  get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
}) : x)(function(x) {
  if (typeof require !== "undefined") return require.apply(this, arguments);
  throw Error('Dynamic require of "' + x + '" is not supported');
});
var __commonJS = (cb, mod) => function __require2() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// node_modules/ws/lib/constants.js
var require_constants = __commonJS({
  "node_modules/ws/lib/constants.js"(exports, module) {
    "use strict";
    var BINARY_TYPES = ["nodebuffer", "arraybuffer", "fragments"];
    var hasBlob = typeof Blob !== "undefined";
    if (hasBlob) BINARY_TYPES.push("blob");
    module.exports = {
      BINARY_TYPES,
      CLOSE_TIMEOUT: 3e4,
      EMPTY_BUFFER: Buffer.alloc(0),
      GUID: "258EAFA5-E914-47DA-95CA-C5AB0DC85B11",
      hasBlob,
      kForOnEventAttribute: /* @__PURE__ */ Symbol("kIsForOnEventAttribute"),
      kListener: /* @__PURE__ */ Symbol("kListener"),
      kStatusCode: /* @__PURE__ */ Symbol("status-code"),
      kWebSocket: /* @__PURE__ */ Symbol("websocket"),
      NOOP: () => {
      }
    };
  }
});

// node_modules/ws/lib/buffer-util.js
var require_buffer_util = __commonJS({
  "node_modules/ws/lib/buffer-util.js"(exports, module) {
    "use strict";
    var { EMPTY_BUFFER } = require_constants();
    var FastBuffer = Buffer[Symbol.species];
    function concat(list, totalLength) {
      if (list.length === 0) return EMPTY_BUFFER;
      if (list.length === 1) return list[0];
      const target = Buffer.allocUnsafe(totalLength);
      let offset = 0;
      for (let i = 0; i < list.length; i++) {
        const buf = list[i];
        target.set(buf, offset);
        offset += buf.length;
      }
      if (offset < totalLength) {
        return new FastBuffer(target.buffer, target.byteOffset, offset);
      }
      return target;
    }
    function _mask(source, mask, output2, offset, length) {
      for (let i = 0; i < length; i++) {
        output2[offset + i] = source[i] ^ mask[i & 3];
      }
    }
    function _unmask(buffer, mask) {
      for (let i = 0; i < buffer.length; i++) {
        buffer[i] ^= mask[i & 3];
      }
    }
    function toArrayBuffer(buf) {
      if (buf.length === buf.buffer.byteLength) {
        return buf.buffer;
      }
      return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length);
    }
    function toBuffer(data) {
      toBuffer.readOnly = true;
      if (Buffer.isBuffer(data)) return data;
      let buf;
      if (data instanceof ArrayBuffer) {
        buf = new FastBuffer(data);
      } else if (ArrayBuffer.isView(data)) {
        buf = new FastBuffer(data.buffer, data.byteOffset, data.byteLength);
      } else {
        buf = Buffer.from(data);
        toBuffer.readOnly = false;
      }
      return buf;
    }
    module.exports = {
      concat,
      mask: _mask,
      toArrayBuffer,
      toBuffer,
      unmask: _unmask
    };
    if (!process.env.WS_NO_BUFFER_UTIL) {
      try {
        const bufferUtil = __require("bufferutil");
        module.exports.mask = function(source, mask, output2, offset, length) {
          if (length < 48) _mask(source, mask, output2, offset, length);
          else bufferUtil.mask(source, mask, output2, offset, length);
        };
        module.exports.unmask = function(buffer, mask) {
          if (buffer.length < 32) _unmask(buffer, mask);
          else bufferUtil.unmask(buffer, mask);
        };
      } catch (e) {
      }
    }
  }
});

// node_modules/ws/lib/limiter.js
var require_limiter = __commonJS({
  "node_modules/ws/lib/limiter.js"(exports, module) {
    "use strict";
    var kDone = /* @__PURE__ */ Symbol("kDone");
    var kRun = /* @__PURE__ */ Symbol("kRun");
    var Limiter = class {
      /**
       * Creates a new `Limiter`.
       *
       * @param {Number} [concurrency=Infinity] The maximum number of jobs allowed
       *     to run concurrently
       */
      constructor(concurrency) {
        this[kDone] = () => {
          this.pending--;
          this[kRun]();
        };
        this.concurrency = concurrency || Infinity;
        this.jobs = [];
        this.pending = 0;
      }
      /**
       * Adds a job to the queue.
       *
       * @param {Function} job The job to run
       * @public
       */
      add(job) {
        this.jobs.push(job);
        this[kRun]();
      }
      /**
       * Removes a job from the queue and runs it if possible.
       *
       * @private
       */
      [kRun]() {
        if (this.pending === this.concurrency) return;
        if (this.jobs.length) {
          const job = this.jobs.shift();
          this.pending++;
          job(this[kDone]);
        }
      }
    };
    module.exports = Limiter;
  }
});

// node_modules/ws/lib/permessage-deflate.js
var require_permessage_deflate = __commonJS({
  "node_modules/ws/lib/permessage-deflate.js"(exports, module) {
    "use strict";
    var zlib = __require("zlib");
    var bufferUtil = require_buffer_util();
    var Limiter = require_limiter();
    var { kStatusCode } = require_constants();
    var FastBuffer = Buffer[Symbol.species];
    var TRAILER = Buffer.from([0, 0, 255, 255]);
    var kPerMessageDeflate = /* @__PURE__ */ Symbol("permessage-deflate");
    var kTotalLength = /* @__PURE__ */ Symbol("total-length");
    var kCallback = /* @__PURE__ */ Symbol("callback");
    var kBuffers = /* @__PURE__ */ Symbol("buffers");
    var kError = /* @__PURE__ */ Symbol("error");
    var zlibLimiter;
    var PerMessageDeflate2 = class {
      /**
       * Creates a PerMessageDeflate instance.
       *
       * @param {Object} [options] Configuration options
       * @param {(Boolean|Number)} [options.clientMaxWindowBits] Advertise support
       *     for, or request, a custom client window size
       * @param {Boolean} [options.clientNoContextTakeover=false] Advertise/
       *     acknowledge disabling of client context takeover
       * @param {Number} [options.concurrencyLimit=10] The number of concurrent
       *     calls to zlib
       * @param {Boolean} [options.isServer=false] Create the instance in either
       *     server or client mode
       * @param {Number} [options.maxPayload=0] The maximum allowed message length
       * @param {(Boolean|Number)} [options.serverMaxWindowBits] Request/confirm the
       *     use of a custom server window size
       * @param {Boolean} [options.serverNoContextTakeover=false] Request/accept
       *     disabling of server context takeover
       * @param {Number} [options.threshold=1024] Size (in bytes) below which
       *     messages should not be compressed if context takeover is disabled
       * @param {Object} [options.zlibDeflateOptions] Options to pass to zlib on
       *     deflate
       * @param {Object} [options.zlibInflateOptions] Options to pass to zlib on
       *     inflate
       */
      constructor(options) {
        this._options = options || {};
        this._threshold = this._options.threshold !== void 0 ? this._options.threshold : 1024;
        this._maxPayload = this._options.maxPayload | 0;
        this._isServer = !!this._options.isServer;
        this._deflate = null;
        this._inflate = null;
        this.params = null;
        if (!zlibLimiter) {
          const concurrency = this._options.concurrencyLimit !== void 0 ? this._options.concurrencyLimit : 10;
          zlibLimiter = new Limiter(concurrency);
        }
      }
      /**
       * @type {String}
       */
      static get extensionName() {
        return "permessage-deflate";
      }
      /**
       * Create an extension negotiation offer.
       *
       * @return {Object} Extension parameters
       * @public
       */
      offer() {
        const params = {};
        if (this._options.serverNoContextTakeover) {
          params.server_no_context_takeover = true;
        }
        if (this._options.clientNoContextTakeover) {
          params.client_no_context_takeover = true;
        }
        if (this._options.serverMaxWindowBits) {
          params.server_max_window_bits = this._options.serverMaxWindowBits;
        }
        if (this._options.clientMaxWindowBits) {
          params.client_max_window_bits = this._options.clientMaxWindowBits;
        } else if (this._options.clientMaxWindowBits == null) {
          params.client_max_window_bits = true;
        }
        return params;
      }
      /**
       * Accept an extension negotiation offer/response.
       *
       * @param {Array} configurations The extension negotiation offers/reponse
       * @return {Object} Accepted configuration
       * @public
       */
      accept(configurations) {
        configurations = this.normalizeParams(configurations);
        this.params = this._isServer ? this.acceptAsServer(configurations) : this.acceptAsClient(configurations);
        return this.params;
      }
      /**
       * Releases all resources used by the extension.
       *
       * @public
       */
      cleanup() {
        if (this._inflate) {
          this._inflate.close();
          this._inflate = null;
        }
        if (this._deflate) {
          const callback = this._deflate[kCallback];
          this._deflate.close();
          this._deflate = null;
          if (callback) {
            callback(
              new Error(
                "The deflate stream was closed while data was being processed"
              )
            );
          }
        }
      }
      /**
       *  Accept an extension negotiation offer.
       *
       * @param {Array} offers The extension negotiation offers
       * @return {Object} Accepted configuration
       * @private
       */
      acceptAsServer(offers) {
        const opts = this._options;
        const accepted = offers.find((params) => {
          if (opts.serverNoContextTakeover === false && params.server_no_context_takeover || params.server_max_window_bits && (opts.serverMaxWindowBits === false || typeof opts.serverMaxWindowBits === "number" && opts.serverMaxWindowBits > params.server_max_window_bits) || typeof opts.clientMaxWindowBits === "number" && (typeof params.client_max_window_bits === "number" ? opts.clientMaxWindowBits > params.client_max_window_bits : !params.client_max_window_bits)) {
            return false;
          }
          return true;
        });
        if (!accepted) {
          throw new Error("None of the extension offers can be accepted");
        }
        if (opts.serverNoContextTakeover) {
          accepted.server_no_context_takeover = true;
        }
        if (opts.clientNoContextTakeover) {
          accepted.client_no_context_takeover = true;
        }
        if (typeof opts.serverMaxWindowBits === "number") {
          accepted.server_max_window_bits = opts.serverMaxWindowBits;
        }
        if (typeof opts.clientMaxWindowBits === "number") {
          accepted.client_max_window_bits = opts.clientMaxWindowBits;
        } else if (accepted.client_max_window_bits === true || opts.clientMaxWindowBits === false) {
          delete accepted.client_max_window_bits;
        }
        return accepted;
      }
      /**
       * Accept the extension negotiation response.
       *
       * @param {Array} response The extension negotiation response
       * @return {Object} Accepted configuration
       * @private
       */
      acceptAsClient(response) {
        const params = response[0];
        if (this._options.clientNoContextTakeover === false && params.client_no_context_takeover) {
          throw new Error('Unexpected parameter "client_no_context_takeover"');
        }
        if (!params.client_max_window_bits) {
          if (typeof this._options.clientMaxWindowBits === "number") {
            params.client_max_window_bits = this._options.clientMaxWindowBits;
          }
        } else if (this._options.clientMaxWindowBits === false || typeof this._options.clientMaxWindowBits === "number" && params.client_max_window_bits > this._options.clientMaxWindowBits) {
          throw new Error(
            'Unexpected or invalid parameter "client_max_window_bits"'
          );
        }
        return params;
      }
      /**
       * Normalize parameters.
       *
       * @param {Array} configurations The extension negotiation offers/reponse
       * @return {Array} The offers/response with normalized parameters
       * @private
       */
      normalizeParams(configurations) {
        configurations.forEach((params) => {
          Object.keys(params).forEach((key) => {
            let value = params[key];
            if (value.length > 1) {
              throw new Error(`Parameter "${key}" must have only a single value`);
            }
            value = value[0];
            if (key === "client_max_window_bits") {
              if (value !== true) {
                const num = +value;
                if (!Number.isInteger(num) || num < 8 || num > 15) {
                  throw new TypeError(
                    `Invalid value for parameter "${key}": ${value}`
                  );
                }
                value = num;
              } else if (!this._isServer) {
                throw new TypeError(
                  `Invalid value for parameter "${key}": ${value}`
                );
              }
            } else if (key === "server_max_window_bits") {
              const num = +value;
              if (!Number.isInteger(num) || num < 8 || num > 15) {
                throw new TypeError(
                  `Invalid value for parameter "${key}": ${value}`
                );
              }
              value = num;
            } else if (key === "client_no_context_takeover" || key === "server_no_context_takeover") {
              if (value !== true) {
                throw new TypeError(
                  `Invalid value for parameter "${key}": ${value}`
                );
              }
            } else {
              throw new Error(`Unknown parameter "${key}"`);
            }
            params[key] = value;
          });
        });
        return configurations;
      }
      /**
       * Decompress data. Concurrency limited.
       *
       * @param {Buffer} data Compressed data
       * @param {Boolean} fin Specifies whether or not this is the last fragment
       * @param {Function} callback Callback
       * @public
       */
      decompress(data, fin, callback) {
        zlibLimiter.add((done) => {
          this._decompress(data, fin, (err, result) => {
            done();
            callback(err, result);
          });
        });
      }
      /**
       * Compress data. Concurrency limited.
       *
       * @param {(Buffer|String)} data Data to compress
       * @param {Boolean} fin Specifies whether or not this is the last fragment
       * @param {Function} callback Callback
       * @public
       */
      compress(data, fin, callback) {
        zlibLimiter.add((done) => {
          this._compress(data, fin, (err, result) => {
            done();
            callback(err, result);
          });
        });
      }
      /**
       * Decompress data.
       *
       * @param {Buffer} data Compressed data
       * @param {Boolean} fin Specifies whether or not this is the last fragment
       * @param {Function} callback Callback
       * @private
       */
      _decompress(data, fin, callback) {
        const endpoint = this._isServer ? "client" : "server";
        if (!this._inflate) {
          const key = `${endpoint}_max_window_bits`;
          const windowBits = typeof this.params[key] !== "number" ? zlib.Z_DEFAULT_WINDOWBITS : this.params[key];
          this._inflate = zlib.createInflateRaw({
            ...this._options.zlibInflateOptions,
            windowBits
          });
          this._inflate[kPerMessageDeflate] = this;
          this._inflate[kTotalLength] = 0;
          this._inflate[kBuffers] = [];
          this._inflate.on("error", inflateOnError);
          this._inflate.on("data", inflateOnData);
        }
        this._inflate[kCallback] = callback;
        this._inflate.write(data);
        if (fin) this._inflate.write(TRAILER);
        this._inflate.flush(() => {
          const err = this._inflate[kError];
          if (err) {
            this._inflate.close();
            this._inflate = null;
            callback(err);
            return;
          }
          const data2 = bufferUtil.concat(
            this._inflate[kBuffers],
            this._inflate[kTotalLength]
          );
          if (this._inflate._readableState.endEmitted) {
            this._inflate.close();
            this._inflate = null;
          } else {
            this._inflate[kTotalLength] = 0;
            this._inflate[kBuffers] = [];
            if (fin && this.params[`${endpoint}_no_context_takeover`]) {
              this._inflate.reset();
            }
          }
          callback(null, data2);
        });
      }
      /**
       * Compress data.
       *
       * @param {(Buffer|String)} data Data to compress
       * @param {Boolean} fin Specifies whether or not this is the last fragment
       * @param {Function} callback Callback
       * @private
       */
      _compress(data, fin, callback) {
        const endpoint = this._isServer ? "server" : "client";
        if (!this._deflate) {
          const key = `${endpoint}_max_window_bits`;
          const windowBits = typeof this.params[key] !== "number" ? zlib.Z_DEFAULT_WINDOWBITS : this.params[key];
          this._deflate = zlib.createDeflateRaw({
            ...this._options.zlibDeflateOptions,
            windowBits
          });
          this._deflate[kTotalLength] = 0;
          this._deflate[kBuffers] = [];
          this._deflate.on("data", deflateOnData);
        }
        this._deflate[kCallback] = callback;
        this._deflate.write(data);
        this._deflate.flush(zlib.Z_SYNC_FLUSH, () => {
          if (!this._deflate) {
            return;
          }
          let data2 = bufferUtil.concat(
            this._deflate[kBuffers],
            this._deflate[kTotalLength]
          );
          if (fin) {
            data2 = new FastBuffer(data2.buffer, data2.byteOffset, data2.length - 4);
          }
          this._deflate[kCallback] = null;
          this._deflate[kTotalLength] = 0;
          this._deflate[kBuffers] = [];
          if (fin && this.params[`${endpoint}_no_context_takeover`]) {
            this._deflate.reset();
          }
          callback(null, data2);
        });
      }
    };
    module.exports = PerMessageDeflate2;
    function deflateOnData(chunk) {
      this[kBuffers].push(chunk);
      this[kTotalLength] += chunk.length;
    }
    function inflateOnData(chunk) {
      this[kTotalLength] += chunk.length;
      if (this[kPerMessageDeflate]._maxPayload < 1 || this[kTotalLength] <= this[kPerMessageDeflate]._maxPayload) {
        this[kBuffers].push(chunk);
        return;
      }
      this[kError] = new RangeError("Max payload size exceeded");
      this[kError].code = "WS_ERR_UNSUPPORTED_MESSAGE_LENGTH";
      this[kError][kStatusCode] = 1009;
      this.removeListener("data", inflateOnData);
      this.reset();
    }
    function inflateOnError(err) {
      this[kPerMessageDeflate]._inflate = null;
      if (this[kError]) {
        this[kCallback](this[kError]);
        return;
      }
      err[kStatusCode] = 1007;
      this[kCallback](err);
    }
  }
});

// node_modules/ws/lib/validation.js
var require_validation = __commonJS({
  "node_modules/ws/lib/validation.js"(exports, module) {
    "use strict";
    var { isUtf8 } = __require("buffer");
    var { hasBlob } = require_constants();
    var tokenChars = [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      // 0 - 15
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      // 16 - 31
      0,
      1,
      0,
      1,
      1,
      1,
      1,
      1,
      0,
      0,
      1,
      1,
      0,
      1,
      1,
      0,
      // 32 - 47
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      0,
      0,
      0,
      0,
      0,
      0,
      // 48 - 63
      0,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      // 64 - 79
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      0,
      0,
      0,
      1,
      1,
      // 80 - 95
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      // 96 - 111
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      1,
      0,
      1,
      0,
      1,
      0
      // 112 - 127
    ];
    function isValidStatusCode(code) {
      return code >= 1e3 && code <= 1014 && code !== 1004 && code !== 1005 && code !== 1006 || code >= 3e3 && code <= 4999;
    }
    function _isValidUTF8(buf) {
      const len = buf.length;
      let i = 0;
      while (i < len) {
        if ((buf[i] & 128) === 0) {
          i++;
        } else if ((buf[i] & 224) === 192) {
          if (i + 1 === len || (buf[i + 1] & 192) !== 128 || (buf[i] & 254) === 192) {
            return false;
          }
          i += 2;
        } else if ((buf[i] & 240) === 224) {
          if (i + 2 >= len || (buf[i + 1] & 192) !== 128 || (buf[i + 2] & 192) !== 128 || buf[i] === 224 && (buf[i + 1] & 224) === 128 || // Overlong
          buf[i] === 237 && (buf[i + 1] & 224) === 160) {
            return false;
          }
          i += 3;
        } else if ((buf[i] & 248) === 240) {
          if (i + 3 >= len || (buf[i + 1] & 192) !== 128 || (buf[i + 2] & 192) !== 128 || (buf[i + 3] & 192) !== 128 || buf[i] === 240 && (buf[i + 1] & 240) === 128 || // Overlong
          buf[i] === 244 && buf[i + 1] > 143 || buf[i] > 244) {
            return false;
          }
          i += 4;
        } else {
          return false;
        }
      }
      return true;
    }
    function isBlob(value) {
      return hasBlob && typeof value === "object" && typeof value.arrayBuffer === "function" && typeof value.type === "string" && typeof value.stream === "function" && (value[Symbol.toStringTag] === "Blob" || value[Symbol.toStringTag] === "File");
    }
    module.exports = {
      isBlob,
      isValidStatusCode,
      isValidUTF8: _isValidUTF8,
      tokenChars
    };
    if (isUtf8) {
      module.exports.isValidUTF8 = function(buf) {
        return buf.length < 24 ? _isValidUTF8(buf) : isUtf8(buf);
      };
    } else if (!process.env.WS_NO_UTF_8_VALIDATE) {
      try {
        const isValidUTF8 = __require("utf-8-validate");
        module.exports.isValidUTF8 = function(buf) {
          return buf.length < 32 ? _isValidUTF8(buf) : isValidUTF8(buf);
        };
      } catch (e) {
      }
    }
  }
});

// node_modules/ws/lib/receiver.js
var require_receiver = __commonJS({
  "node_modules/ws/lib/receiver.js"(exports, module) {
    "use strict";
    var { Writable } = __require("stream");
    var PerMessageDeflate2 = require_permessage_deflate();
    var {
      BINARY_TYPES,
      EMPTY_BUFFER,
      kStatusCode,
      kWebSocket
    } = require_constants();
    var { concat, toArrayBuffer, unmask } = require_buffer_util();
    var { isValidStatusCode, isValidUTF8 } = require_validation();
    var FastBuffer = Buffer[Symbol.species];
    var GET_INFO = 0;
    var GET_PAYLOAD_LENGTH_16 = 1;
    var GET_PAYLOAD_LENGTH_64 = 2;
    var GET_MASK = 3;
    var GET_DATA = 4;
    var INFLATING = 5;
    var DEFER_EVENT = 6;
    var Receiver2 = class extends Writable {
      /**
       * Creates a Receiver instance.
       *
       * @param {Object} [options] Options object
       * @param {Boolean} [options.allowSynchronousEvents=true] Specifies whether
       *     any of the `'message'`, `'ping'`, and `'pong'` events can be emitted
       *     multiple times in the same tick
       * @param {String} [options.binaryType=nodebuffer] The type for binary data
       * @param {Object} [options.extensions] An object containing the negotiated
       *     extensions
       * @param {Boolean} [options.isServer=false] Specifies whether to operate in
       *     client or server mode
       * @param {Number} [options.maxBufferedChunks=0] The maximum number of
       *     buffered data chunks
       * @param {Number} [options.maxFragments=0] The maximum number of message
       *     fragments
       * @param {Number} [options.maxPayload=0] The maximum allowed message length
       * @param {Boolean} [options.skipUTF8Validation=false] Specifies whether or
       *     not to skip UTF-8 validation for text and close messages
       */
      constructor(options = {}) {
        super();
        this._allowSynchronousEvents = options.allowSynchronousEvents !== void 0 ? options.allowSynchronousEvents : true;
        this._binaryType = options.binaryType || BINARY_TYPES[0];
        this._extensions = options.extensions || {};
        this._isServer = !!options.isServer;
        this._maxBufferedChunks = options.maxBufferedChunks | 0;
        this._maxFragments = options.maxFragments | 0;
        this._maxPayload = options.maxPayload | 0;
        this._skipUTF8Validation = !!options.skipUTF8Validation;
        this[kWebSocket] = void 0;
        this._bufferedBytes = 0;
        this._buffers = [];
        this._compressed = false;
        this._payloadLength = 0;
        this._mask = void 0;
        this._fragmented = 0;
        this._masked = false;
        this._fin = false;
        this._opcode = 0;
        this._totalPayloadLength = 0;
        this._messageLength = 0;
        this._numFragments = 0;
        this._fragments = [];
        this._errored = false;
        this._loop = false;
        this._state = GET_INFO;
      }
      /**
       * Implements `Writable.prototype._write()`.
       *
       * @param {Buffer} chunk The chunk of data to write
       * @param {String} encoding The character encoding of `chunk`
       * @param {Function} cb Callback
       * @private
       */
      _write(chunk, encoding, cb) {
        if (this._opcode === 8 && this._state == GET_INFO) return cb();
        if (this._maxBufferedChunks > 0 && this._buffers.length >= this._maxBufferedChunks) {
          cb(
            this.createError(
              RangeError,
              "Too many buffered chunks",
              false,
              1008,
              "WS_ERR_TOO_MANY_BUFFERED_PARTS"
            )
          );
          return;
        }
        this._bufferedBytes += chunk.length;
        this._buffers.push(chunk);
        this.startLoop(cb);
      }
      /**
       * Consumes `n` bytes from the buffered data.
       *
       * @param {Number} n The number of bytes to consume
       * @return {Buffer} The consumed bytes
       * @private
       */
      consume(n) {
        this._bufferedBytes -= n;
        if (n === this._buffers[0].length) return this._buffers.shift();
        if (n < this._buffers[0].length) {
          const buf = this._buffers[0];
          this._buffers[0] = new FastBuffer(
            buf.buffer,
            buf.byteOffset + n,
            buf.length - n
          );
          return new FastBuffer(buf.buffer, buf.byteOffset, n);
        }
        const dst = Buffer.allocUnsafe(n);
        do {
          const buf = this._buffers[0];
          const offset = dst.length - n;
          if (n >= buf.length) {
            dst.set(this._buffers.shift(), offset);
          } else {
            dst.set(new Uint8Array(buf.buffer, buf.byteOffset, n), offset);
            this._buffers[0] = new FastBuffer(
              buf.buffer,
              buf.byteOffset + n,
              buf.length - n
            );
          }
          n -= buf.length;
        } while (n > 0);
        return dst;
      }
      /**
       * Starts the parsing loop.
       *
       * @param {Function} cb Callback
       * @private
       */
      startLoop(cb) {
        this._loop = true;
        do {
          switch (this._state) {
            case GET_INFO:
              this.getInfo(cb);
              break;
            case GET_PAYLOAD_LENGTH_16:
              this.getPayloadLength16(cb);
              break;
            case GET_PAYLOAD_LENGTH_64:
              this.getPayloadLength64(cb);
              break;
            case GET_MASK:
              this.getMask();
              break;
            case GET_DATA:
              this.getData(cb);
              break;
            case INFLATING:
            case DEFER_EVENT:
              this._loop = false;
              return;
          }
        } while (this._loop);
        if (!this._errored) cb();
      }
      /**
       * Reads the first two bytes of a frame.
       *
       * @param {Function} cb Callback
       * @private
       */
      getInfo(cb) {
        if (this._bufferedBytes < 2) {
          this._loop = false;
          return;
        }
        const buf = this.consume(2);
        if ((buf[0] & 48) !== 0) {
          const error = this.createError(
            RangeError,
            "RSV2 and RSV3 must be clear",
            true,
            1002,
            "WS_ERR_UNEXPECTED_RSV_2_3"
          );
          cb(error);
          return;
        }
        const compressed = (buf[0] & 64) === 64;
        if (compressed && !this._extensions[PerMessageDeflate2.extensionName]) {
          const error = this.createError(
            RangeError,
            "RSV1 must be clear",
            true,
            1002,
            "WS_ERR_UNEXPECTED_RSV_1"
          );
          cb(error);
          return;
        }
        this._fin = (buf[0] & 128) === 128;
        this._opcode = buf[0] & 15;
        this._payloadLength = buf[1] & 127;
        if (this._opcode === 0) {
          if (compressed) {
            const error = this.createError(
              RangeError,
              "RSV1 must be clear",
              true,
              1002,
              "WS_ERR_UNEXPECTED_RSV_1"
            );
            cb(error);
            return;
          }
          if (!this._fragmented) {
            const error = this.createError(
              RangeError,
              "invalid opcode 0",
              true,
              1002,
              "WS_ERR_INVALID_OPCODE"
            );
            cb(error);
            return;
          }
          this._opcode = this._fragmented;
        } else if (this._opcode === 1 || this._opcode === 2) {
          if (this._fragmented) {
            const error = this.createError(
              RangeError,
              `invalid opcode ${this._opcode}`,
              true,
              1002,
              "WS_ERR_INVALID_OPCODE"
            );
            cb(error);
            return;
          }
          this._compressed = compressed;
        } else if (this._opcode > 7 && this._opcode < 11) {
          if (!this._fin) {
            const error = this.createError(
              RangeError,
              "FIN must be set",
              true,
              1002,
              "WS_ERR_EXPECTED_FIN"
            );
            cb(error);
            return;
          }
          if (compressed) {
            const error = this.createError(
              RangeError,
              "RSV1 must be clear",
              true,
              1002,
              "WS_ERR_UNEXPECTED_RSV_1"
            );
            cb(error);
            return;
          }
          if (this._payloadLength > 125 || this._opcode === 8 && this._payloadLength === 1) {
            const error = this.createError(
              RangeError,
              `invalid payload length ${this._payloadLength}`,
              true,
              1002,
              "WS_ERR_INVALID_CONTROL_PAYLOAD_LENGTH"
            );
            cb(error);
            return;
          }
        } else {
          const error = this.createError(
            RangeError,
            `invalid opcode ${this._opcode}`,
            true,
            1002,
            "WS_ERR_INVALID_OPCODE"
          );
          cb(error);
          return;
        }
        if (!this._fin && !this._fragmented) this._fragmented = this._opcode;
        this._masked = (buf[1] & 128) === 128;
        if (this._isServer) {
          if (!this._masked) {
            const error = this.createError(
              RangeError,
              "MASK must be set",
              true,
              1002,
              "WS_ERR_EXPECTED_MASK"
            );
            cb(error);
            return;
          }
        } else if (this._masked) {
          const error = this.createError(
            RangeError,
            "MASK must be clear",
            true,
            1002,
            "WS_ERR_UNEXPECTED_MASK"
          );
          cb(error);
          return;
        }
        if (this._payloadLength === 126) this._state = GET_PAYLOAD_LENGTH_16;
        else if (this._payloadLength === 127) this._state = GET_PAYLOAD_LENGTH_64;
        else this.haveLength(cb);
      }
      /**
       * Gets extended payload length (7+16).
       *
       * @param {Function} cb Callback
       * @private
       */
      getPayloadLength16(cb) {
        if (this._bufferedBytes < 2) {
          this._loop = false;
          return;
        }
        this._payloadLength = this.consume(2).readUInt16BE(0);
        this.haveLength(cb);
      }
      /**
       * Gets extended payload length (7+64).
       *
       * @param {Function} cb Callback
       * @private
       */
      getPayloadLength64(cb) {
        if (this._bufferedBytes < 8) {
          this._loop = false;
          return;
        }
        const buf = this.consume(8);
        const num = buf.readUInt32BE(0);
        if (num > Math.pow(2, 53 - 32) - 1) {
          const error = this.createError(
            RangeError,
            "Unsupported WebSocket frame: payload length > 2^53 - 1",
            false,
            1009,
            "WS_ERR_UNSUPPORTED_DATA_PAYLOAD_LENGTH"
          );
          cb(error);
          return;
        }
        this._payloadLength = num * Math.pow(2, 32) + buf.readUInt32BE(4);
        this.haveLength(cb);
      }
      /**
       * Payload length has been read.
       *
       * @param {Function} cb Callback
       * @private
       */
      haveLength(cb) {
        if (this._payloadLength && this._opcode < 8) {
          this._totalPayloadLength += this._payloadLength;
          if (this._totalPayloadLength > this._maxPayload && this._maxPayload > 0) {
            const error = this.createError(
              RangeError,
              "Max payload size exceeded",
              false,
              1009,
              "WS_ERR_UNSUPPORTED_MESSAGE_LENGTH"
            );
            cb(error);
            return;
          }
        }
        if (this._masked) this._state = GET_MASK;
        else this._state = GET_DATA;
      }
      /**
       * Reads mask bytes.
       *
       * @private
       */
      getMask() {
        if (this._bufferedBytes < 4) {
          this._loop = false;
          return;
        }
        this._mask = this.consume(4);
        this._state = GET_DATA;
      }
      /**
       * Reads data bytes.
       *
       * @param {Function} cb Callback
       * @private
       */
      getData(cb) {
        let data = EMPTY_BUFFER;
        if (this._payloadLength) {
          if (this._bufferedBytes < this._payloadLength) {
            this._loop = false;
            return;
          }
          data = this.consume(this._payloadLength);
          if (this._masked && (this._mask[0] | this._mask[1] | this._mask[2] | this._mask[3]) !== 0) {
            unmask(data, this._mask);
          }
        }
        if (this._opcode > 7) {
          this.controlMessage(data, cb);
          return;
        }
        if (this._maxFragments > 0 && ++this._numFragments > this._maxFragments) {
          const error = this.createError(
            RangeError,
            "Too many message fragments",
            false,
            1008,
            "WS_ERR_TOO_MANY_BUFFERED_PARTS"
          );
          cb(error);
          return;
        }
        if (this._compressed) {
          this._state = INFLATING;
          this.decompress(data, cb);
          return;
        }
        if (data.length) {
          this._messageLength = this._totalPayloadLength;
          this._fragments.push(data);
        }
        this.dataMessage(cb);
      }
      /**
       * Decompresses data.
       *
       * @param {Buffer} data Compressed data
       * @param {Function} cb Callback
       * @private
       */
      decompress(data, cb) {
        const perMessageDeflate = this._extensions[PerMessageDeflate2.extensionName];
        perMessageDeflate.decompress(data, this._fin, (err, buf) => {
          if (err) return cb(err);
          if (buf.length) {
            this._messageLength += buf.length;
            if (this._messageLength > this._maxPayload && this._maxPayload > 0) {
              const error = this.createError(
                RangeError,
                "Max payload size exceeded",
                false,
                1009,
                "WS_ERR_UNSUPPORTED_MESSAGE_LENGTH"
              );
              cb(error);
              return;
            }
            this._fragments.push(buf);
          }
          this.dataMessage(cb);
          if (this._state === GET_INFO) this.startLoop(cb);
        });
      }
      /**
       * Handles a data message.
       *
       * @param {Function} cb Callback
       * @private
       */
      dataMessage(cb) {
        if (!this._fin) {
          this._state = GET_INFO;
          return;
        }
        const messageLength = this._messageLength;
        const fragments = this._fragments;
        this._totalPayloadLength = 0;
        this._messageLength = 0;
        this._fragmented = 0;
        this._numFragments = 0;
        this._fragments = [];
        if (this._opcode === 2) {
          let data;
          if (this._binaryType === "nodebuffer") {
            data = concat(fragments, messageLength);
          } else if (this._binaryType === "arraybuffer") {
            data = toArrayBuffer(concat(fragments, messageLength));
          } else if (this._binaryType === "blob") {
            data = new Blob(fragments);
          } else {
            data = fragments;
          }
          if (this._allowSynchronousEvents) {
            this.emit("message", data, true);
            this._state = GET_INFO;
          } else {
            this._state = DEFER_EVENT;
            setImmediate(() => {
              this.emit("message", data, true);
              this._state = GET_INFO;
              this.startLoop(cb);
            });
          }
        } else {
          const buf = concat(fragments, messageLength);
          if (!this._skipUTF8Validation && !isValidUTF8(buf)) {
            const error = this.createError(
              Error,
              "invalid UTF-8 sequence",
              true,
              1007,
              "WS_ERR_INVALID_UTF8"
            );
            cb(error);
            return;
          }
          if (this._state === INFLATING || this._allowSynchronousEvents) {
            this.emit("message", buf, false);
            this._state = GET_INFO;
          } else {
            this._state = DEFER_EVENT;
            setImmediate(() => {
              this.emit("message", buf, false);
              this._state = GET_INFO;
              this.startLoop(cb);
            });
          }
        }
      }
      /**
       * Handles a control message.
       *
       * @param {Buffer} data Data to handle
       * @return {(Error|RangeError|undefined)} A possible error
       * @private
       */
      controlMessage(data, cb) {
        if (this._opcode === 8) {
          if (data.length === 0) {
            this._loop = false;
            this.emit("conclude", 1005, EMPTY_BUFFER);
            this.end();
          } else {
            const code = data.readUInt16BE(0);
            if (!isValidStatusCode(code)) {
              const error = this.createError(
                RangeError,
                `invalid status code ${code}`,
                true,
                1002,
                "WS_ERR_INVALID_CLOSE_CODE"
              );
              cb(error);
              return;
            }
            const buf = new FastBuffer(
              data.buffer,
              data.byteOffset + 2,
              data.length - 2
            );
            if (!this._skipUTF8Validation && !isValidUTF8(buf)) {
              const error = this.createError(
                Error,
                "invalid UTF-8 sequence",
                true,
                1007,
                "WS_ERR_INVALID_UTF8"
              );
              cb(error);
              return;
            }
            this._loop = false;
            this.emit("conclude", code, buf);
            this.end();
          }
          this._state = GET_INFO;
          return;
        }
        if (this._allowSynchronousEvents) {
          this.emit(this._opcode === 9 ? "ping" : "pong", data);
          this._state = GET_INFO;
        } else {
          this._state = DEFER_EVENT;
          setImmediate(() => {
            this.emit(this._opcode === 9 ? "ping" : "pong", data);
            this._state = GET_INFO;
            this.startLoop(cb);
          });
        }
      }
      /**
       * Builds an error object.
       *
       * @param {function(new:Error|RangeError)} ErrorCtor The error constructor
       * @param {String} message The error message
       * @param {Boolean} prefix Specifies whether or not to add a default prefix to
       *     `message`
       * @param {Number} statusCode The status code
       * @param {String} errorCode The exposed error code
       * @return {(Error|RangeError)} The error
       * @private
       */
      createError(ErrorCtor, message, prefix, statusCode, errorCode) {
        this._loop = false;
        this._errored = true;
        const err = new ErrorCtor(
          prefix ? `Invalid WebSocket frame: ${message}` : message
        );
        Error.captureStackTrace(err, this.createError);
        err.code = errorCode;
        err[kStatusCode] = statusCode;
        return err;
      }
    };
    module.exports = Receiver2;
  }
});

// node_modules/ws/lib/sender.js
var require_sender = __commonJS({
  "node_modules/ws/lib/sender.js"(exports, module) {
    "use strict";
    var { Duplex } = __require("stream");
    var { randomFillSync } = __require("crypto");
    var {
      types: { isUint8Array }
    } = __require("util");
    var PerMessageDeflate2 = require_permessage_deflate();
    var { EMPTY_BUFFER, kWebSocket, NOOP } = require_constants();
    var { isBlob, isValidStatusCode } = require_validation();
    var { mask: applyMask, toBuffer } = require_buffer_util();
    var kByteLength = /* @__PURE__ */ Symbol("kByteLength");
    var maskBuffer = Buffer.alloc(4);
    var RANDOM_POOL_SIZE = 8 * 1024;
    var randomPool;
    var randomPoolPointer = RANDOM_POOL_SIZE;
    var DEFAULT = 0;
    var DEFLATING = 1;
    var GET_BLOB_DATA = 2;
    var Sender2 = class _Sender {
      /**
       * Creates a Sender instance.
       *
       * @param {Duplex} socket The connection socket
       * @param {Object} [extensions] An object containing the negotiated extensions
       * @param {Function} [generateMask] The function used to generate the masking
       *     key
       */
      constructor(socket2, extensions, generateMask) {
        this._extensions = extensions || {};
        if (generateMask) {
          this._generateMask = generateMask;
          this._maskBuffer = Buffer.alloc(4);
        }
        this._socket = socket2;
        this._firstFragment = true;
        this._compress = false;
        this._bufferedBytes = 0;
        this._queue = [];
        this._state = DEFAULT;
        this.onerror = NOOP;
        this[kWebSocket] = void 0;
      }
      /**
       * Frames a piece of data according to the HyBi WebSocket protocol.
       *
       * @param {(Buffer|String)} data The data to frame
       * @param {Object} options Options object
       * @param {Boolean} [options.fin=false] Specifies whether or not to set the
       *     FIN bit
       * @param {Function} [options.generateMask] The function used to generate the
       *     masking key
       * @param {Boolean} [options.mask=false] Specifies whether or not to mask
       *     `data`
       * @param {Buffer} [options.maskBuffer] The buffer used to store the masking
       *     key
       * @param {Number} options.opcode The opcode
       * @param {Boolean} [options.readOnly=false] Specifies whether `data` can be
       *     modified
       * @param {Boolean} [options.rsv1=false] Specifies whether or not to set the
       *     RSV1 bit
       * @return {(Buffer|String)[]} The framed data
       * @public
       */
      static frame(data, options) {
        let mask;
        let merge = false;
        let offset = 2;
        let skipMasking = false;
        if (options.mask) {
          mask = options.maskBuffer || maskBuffer;
          if (options.generateMask) {
            options.generateMask(mask);
          } else {
            if (randomPoolPointer === RANDOM_POOL_SIZE) {
              if (randomPool === void 0) {
                randomPool = Buffer.alloc(RANDOM_POOL_SIZE);
              }
              randomFillSync(randomPool, 0, RANDOM_POOL_SIZE);
              randomPoolPointer = 0;
            }
            mask[0] = randomPool[randomPoolPointer++];
            mask[1] = randomPool[randomPoolPointer++];
            mask[2] = randomPool[randomPoolPointer++];
            mask[3] = randomPool[randomPoolPointer++];
          }
          skipMasking = (mask[0] | mask[1] | mask[2] | mask[3]) === 0;
          offset = 6;
        }
        let dataLength;
        if (typeof data === "string") {
          if ((!options.mask || skipMasking) && options[kByteLength] !== void 0) {
            dataLength = options[kByteLength];
          } else {
            data = Buffer.from(data);
            dataLength = data.length;
          }
        } else {
          dataLength = data.length;
          merge = options.mask && options.readOnly && !skipMasking;
        }
        let payloadLength = dataLength;
        if (dataLength >= 65536) {
          offset += 8;
          payloadLength = 127;
        } else if (dataLength > 125) {
          offset += 2;
          payloadLength = 126;
        }
        const target = Buffer.allocUnsafe(merge ? dataLength + offset : offset);
        target[0] = options.fin ? options.opcode | 128 : options.opcode;
        if (options.rsv1) target[0] |= 64;
        target[1] = payloadLength;
        if (payloadLength === 126) {
          target.writeUInt16BE(dataLength, 2);
        } else if (payloadLength === 127) {
          target[2] = target[3] = 0;
          target.writeUIntBE(dataLength, 4, 6);
        }
        if (!options.mask) return [target, data];
        target[1] |= 128;
        target[offset - 4] = mask[0];
        target[offset - 3] = mask[1];
        target[offset - 2] = mask[2];
        target[offset - 1] = mask[3];
        if (skipMasking) return [target, data];
        if (merge) {
          applyMask(data, mask, target, offset, dataLength);
          return [target];
        }
        applyMask(data, mask, data, 0, dataLength);
        return [target, data];
      }
      /**
       * Sends a close message to the other peer.
       *
       * @param {Number} [code] The status code component of the body
       * @param {(String|Buffer)} [data] The message component of the body
       * @param {Boolean} [mask=false] Specifies whether or not to mask the message
       * @param {Function} [cb] Callback
       * @public
       */
      close(code, data, mask, cb) {
        let buf;
        if (code === void 0) {
          buf = EMPTY_BUFFER;
        } else if (typeof code !== "number" || !isValidStatusCode(code)) {
          throw new TypeError("First argument must be a valid error code number");
        } else if (data === void 0 || !data.length) {
          buf = Buffer.allocUnsafe(2);
          buf.writeUInt16BE(code, 0);
        } else {
          const length = Buffer.byteLength(data);
          if (length > 123) {
            throw new RangeError("The message must not be greater than 123 bytes");
          }
          buf = Buffer.allocUnsafe(2 + length);
          buf.writeUInt16BE(code, 0);
          if (typeof data === "string") {
            buf.write(data, 2);
          } else if (isUint8Array(data)) {
            buf.set(data, 2);
          } else {
            throw new TypeError("Second argument must be a string or a Uint8Array");
          }
        }
        const options = {
          [kByteLength]: buf.length,
          fin: true,
          generateMask: this._generateMask,
          mask,
          maskBuffer: this._maskBuffer,
          opcode: 8,
          readOnly: false,
          rsv1: false
        };
        if (this._state !== DEFAULT) {
          this.enqueue([this.dispatch, buf, false, options, cb]);
        } else {
          this.sendFrame(_Sender.frame(buf, options), cb);
        }
      }
      /**
       * Sends a ping message to the other peer.
       *
       * @param {*} data The message to send
       * @param {Boolean} [mask=false] Specifies whether or not to mask `data`
       * @param {Function} [cb] Callback
       * @public
       */
      ping(data, mask, cb) {
        let byteLength;
        let readOnly;
        if (typeof data === "string") {
          byteLength = Buffer.byteLength(data);
          readOnly = false;
        } else if (isBlob(data)) {
          byteLength = data.size;
          readOnly = false;
        } else {
          data = toBuffer(data);
          byteLength = data.length;
          readOnly = toBuffer.readOnly;
        }
        if (byteLength > 125) {
          throw new RangeError("The data size must not be greater than 125 bytes");
        }
        const options = {
          [kByteLength]: byteLength,
          fin: true,
          generateMask: this._generateMask,
          mask,
          maskBuffer: this._maskBuffer,
          opcode: 9,
          readOnly,
          rsv1: false
        };
        if (isBlob(data)) {
          if (this._state !== DEFAULT) {
            this.enqueue([this.getBlobData, data, false, options, cb]);
          } else {
            this.getBlobData(data, false, options, cb);
          }
        } else if (this._state !== DEFAULT) {
          this.enqueue([this.dispatch, data, false, options, cb]);
        } else {
          this.sendFrame(_Sender.frame(data, options), cb);
        }
      }
      /**
       * Sends a pong message to the other peer.
       *
       * @param {*} data The message to send
       * @param {Boolean} [mask=false] Specifies whether or not to mask `data`
       * @param {Function} [cb] Callback
       * @public
       */
      pong(data, mask, cb) {
        let byteLength;
        let readOnly;
        if (typeof data === "string") {
          byteLength = Buffer.byteLength(data);
          readOnly = false;
        } else if (isBlob(data)) {
          byteLength = data.size;
          readOnly = false;
        } else {
          data = toBuffer(data);
          byteLength = data.length;
          readOnly = toBuffer.readOnly;
        }
        if (byteLength > 125) {
          throw new RangeError("The data size must not be greater than 125 bytes");
        }
        const options = {
          [kByteLength]: byteLength,
          fin: true,
          generateMask: this._generateMask,
          mask,
          maskBuffer: this._maskBuffer,
          opcode: 10,
          readOnly,
          rsv1: false
        };
        if (isBlob(data)) {
          if (this._state !== DEFAULT) {
            this.enqueue([this.getBlobData, data, false, options, cb]);
          } else {
            this.getBlobData(data, false, options, cb);
          }
        } else if (this._state !== DEFAULT) {
          this.enqueue([this.dispatch, data, false, options, cb]);
        } else {
          this.sendFrame(_Sender.frame(data, options), cb);
        }
      }
      /**
       * Sends a data message to the other peer.
       *
       * @param {*} data The message to send
       * @param {Object} options Options object
       * @param {Boolean} [options.binary=false] Specifies whether `data` is binary
       *     or text
       * @param {Boolean} [options.compress=false] Specifies whether or not to
       *     compress `data`
       * @param {Boolean} [options.fin=false] Specifies whether the fragment is the
       *     last one
       * @param {Boolean} [options.mask=false] Specifies whether or not to mask
       *     `data`
       * @param {Function} [cb] Callback
       * @public
       */
      send(data, options, cb) {
        const perMessageDeflate = this._extensions[PerMessageDeflate2.extensionName];
        let opcode = options.binary ? 2 : 1;
        let rsv1 = options.compress;
        let byteLength;
        let readOnly;
        if (typeof data === "string") {
          byteLength = Buffer.byteLength(data);
          readOnly = false;
        } else if (isBlob(data)) {
          byteLength = data.size;
          readOnly = false;
        } else {
          data = toBuffer(data);
          byteLength = data.length;
          readOnly = toBuffer.readOnly;
        }
        if (this._firstFragment) {
          this._firstFragment = false;
          if (rsv1 && perMessageDeflate && perMessageDeflate.params[perMessageDeflate._isServer ? "server_no_context_takeover" : "client_no_context_takeover"]) {
            rsv1 = byteLength >= perMessageDeflate._threshold;
          }
          this._compress = rsv1;
        } else {
          rsv1 = false;
          opcode = 0;
        }
        if (options.fin) this._firstFragment = true;
        const opts = {
          [kByteLength]: byteLength,
          fin: options.fin,
          generateMask: this._generateMask,
          mask: options.mask,
          maskBuffer: this._maskBuffer,
          opcode,
          readOnly,
          rsv1
        };
        if (isBlob(data)) {
          if (this._state !== DEFAULT) {
            this.enqueue([this.getBlobData, data, this._compress, opts, cb]);
          } else {
            this.getBlobData(data, this._compress, opts, cb);
          }
        } else if (this._state !== DEFAULT) {
          this.enqueue([this.dispatch, data, this._compress, opts, cb]);
        } else {
          this.dispatch(data, this._compress, opts, cb);
        }
      }
      /**
       * Gets the contents of a blob as binary data.
       *
       * @param {Blob} blob The blob
       * @param {Boolean} [compress=false] Specifies whether or not to compress
       *     the data
       * @param {Object} options Options object
       * @param {Boolean} [options.fin=false] Specifies whether or not to set the
       *     FIN bit
       * @param {Function} [options.generateMask] The function used to generate the
       *     masking key
       * @param {Boolean} [options.mask=false] Specifies whether or not to mask
       *     `data`
       * @param {Buffer} [options.maskBuffer] The buffer used to store the masking
       *     key
       * @param {Number} options.opcode The opcode
       * @param {Boolean} [options.readOnly=false] Specifies whether `data` can be
       *     modified
       * @param {Boolean} [options.rsv1=false] Specifies whether or not to set the
       *     RSV1 bit
       * @param {Function} [cb] Callback
       * @private
       */
      getBlobData(blob, compress, options, cb) {
        this._bufferedBytes += options[kByteLength];
        this._state = GET_BLOB_DATA;
        blob.arrayBuffer().then((arrayBuffer) => {
          if (this._socket.destroyed) {
            const err = new Error(
              "The socket was closed while the blob was being read"
            );
            process.nextTick(callCallbacks, this, err, cb);
            return;
          }
          this._bufferedBytes -= options[kByteLength];
          const data = toBuffer(arrayBuffer);
          if (!compress) {
            this._state = DEFAULT;
            this.sendFrame(_Sender.frame(data, options), cb);
            this.dequeue();
          } else {
            this.dispatch(data, compress, options, cb);
          }
        }).catch((err) => {
          process.nextTick(onError, this, err, cb);
        });
      }
      /**
       * Dispatches a message.
       *
       * @param {(Buffer|String)} data The message to send
       * @param {Boolean} [compress=false] Specifies whether or not to compress
       *     `data`
       * @param {Object} options Options object
       * @param {Boolean} [options.fin=false] Specifies whether or not to set the
       *     FIN bit
       * @param {Function} [options.generateMask] The function used to generate the
       *     masking key
       * @param {Boolean} [options.mask=false] Specifies whether or not to mask
       *     `data`
       * @param {Buffer} [options.maskBuffer] The buffer used to store the masking
       *     key
       * @param {Number} options.opcode The opcode
       * @param {Boolean} [options.readOnly=false] Specifies whether `data` can be
       *     modified
       * @param {Boolean} [options.rsv1=false] Specifies whether or not to set the
       *     RSV1 bit
       * @param {Function} [cb] Callback
       * @private
       */
      dispatch(data, compress, options, cb) {
        if (!compress) {
          this.sendFrame(_Sender.frame(data, options), cb);
          return;
        }
        const perMessageDeflate = this._extensions[PerMessageDeflate2.extensionName];
        this._bufferedBytes += options[kByteLength];
        this._state = DEFLATING;
        perMessageDeflate.compress(data, options.fin, (_, buf) => {
          if (this._socket.destroyed) {
            const err = new Error(
              "The socket was closed while data was being compressed"
            );
            callCallbacks(this, err, cb);
            return;
          }
          this._bufferedBytes -= options[kByteLength];
          this._state = DEFAULT;
          options.readOnly = false;
          this.sendFrame(_Sender.frame(buf, options), cb);
          this.dequeue();
        });
      }
      /**
       * Executes queued send operations.
       *
       * @private
       */
      dequeue() {
        while (this._state === DEFAULT && this._queue.length) {
          const params = this._queue.shift();
          this._bufferedBytes -= params[3][kByteLength];
          Reflect.apply(params[0], this, params.slice(1));
        }
      }
      /**
       * Enqueues a send operation.
       *
       * @param {Array} params Send operation parameters.
       * @private
       */
      enqueue(params) {
        this._bufferedBytes += params[3][kByteLength];
        this._queue.push(params);
      }
      /**
       * Sends a frame.
       *
       * @param {(Buffer | String)[]} list The frame to send
       * @param {Function} [cb] Callback
       * @private
       */
      sendFrame(list, cb) {
        if (list.length === 2) {
          this._socket.cork();
          this._socket.write(list[0]);
          this._socket.write(list[1], cb);
          this._socket.uncork();
        } else {
          this._socket.write(list[0], cb);
        }
      }
    };
    module.exports = Sender2;
    function callCallbacks(sender, err, cb) {
      if (typeof cb === "function") cb(err);
      for (let i = 0; i < sender._queue.length; i++) {
        const params = sender._queue[i];
        const callback = params[params.length - 1];
        if (typeof callback === "function") callback(err);
      }
    }
    function onError(sender, err, cb) {
      callCallbacks(sender, err, cb);
      sender.onerror(err);
    }
  }
});

// node_modules/ws/lib/event-target.js
var require_event_target = __commonJS({
  "node_modules/ws/lib/event-target.js"(exports, module) {
    "use strict";
    var { kForOnEventAttribute, kListener } = require_constants();
    var kCode = /* @__PURE__ */ Symbol("kCode");
    var kData = /* @__PURE__ */ Symbol("kData");
    var kError = /* @__PURE__ */ Symbol("kError");
    var kMessage = /* @__PURE__ */ Symbol("kMessage");
    var kReason = /* @__PURE__ */ Symbol("kReason");
    var kTarget = /* @__PURE__ */ Symbol("kTarget");
    var kType = /* @__PURE__ */ Symbol("kType");
    var kWasClean = /* @__PURE__ */ Symbol("kWasClean");
    var Event = class {
      /**
       * Create a new `Event`.
       *
       * @param {String} type The name of the event
       * @throws {TypeError} If the `type` argument is not specified
       */
      constructor(type) {
        this[kTarget] = null;
        this[kType] = type;
      }
      /**
       * @type {*}
       */
      get target() {
        return this[kTarget];
      }
      /**
       * @type {String}
       */
      get type() {
        return this[kType];
      }
    };
    Object.defineProperty(Event.prototype, "target", { enumerable: true });
    Object.defineProperty(Event.prototype, "type", { enumerable: true });
    var CloseEvent = class extends Event {
      /**
       * Create a new `CloseEvent`.
       *
       * @param {String} type The name of the event
       * @param {Object} [options] A dictionary object that allows for setting
       *     attributes via object members of the same name
       * @param {Number} [options.code=0] The status code explaining why the
       *     connection was closed
       * @param {String} [options.reason=''] A human-readable string explaining why
       *     the connection was closed
       * @param {Boolean} [options.wasClean=false] Indicates whether or not the
       *     connection was cleanly closed
       */
      constructor(type, options = {}) {
        super(type);
        this[kCode] = options.code === void 0 ? 0 : options.code;
        this[kReason] = options.reason === void 0 ? "" : options.reason;
        this[kWasClean] = options.wasClean === void 0 ? false : options.wasClean;
      }
      /**
       * @type {Number}
       */
      get code() {
        return this[kCode];
      }
      /**
       * @type {String}
       */
      get reason() {
        return this[kReason];
      }
      /**
       * @type {Boolean}
       */
      get wasClean() {
        return this[kWasClean];
      }
    };
    Object.defineProperty(CloseEvent.prototype, "code", { enumerable: true });
    Object.defineProperty(CloseEvent.prototype, "reason", { enumerable: true });
    Object.defineProperty(CloseEvent.prototype, "wasClean", { enumerable: true });
    var ErrorEvent = class extends Event {
      /**
       * Create a new `ErrorEvent`.
       *
       * @param {String} type The name of the event
       * @param {Object} [options] A dictionary object that allows for setting
       *     attributes via object members of the same name
       * @param {*} [options.error=null] The error that generated this event
       * @param {String} [options.message=''] The error message
       */
      constructor(type, options = {}) {
        super(type);
        this[kError] = options.error === void 0 ? null : options.error;
        this[kMessage] = options.message === void 0 ? "" : options.message;
      }
      /**
       * @type {*}
       */
      get error() {
        return this[kError];
      }
      /**
       * @type {String}
       */
      get message() {
        return this[kMessage];
      }
    };
    Object.defineProperty(ErrorEvent.prototype, "error", { enumerable: true });
    Object.defineProperty(ErrorEvent.prototype, "message", { enumerable: true });
    var MessageEvent = class extends Event {
      /**
       * Create a new `MessageEvent`.
       *
       * @param {String} type The name of the event
       * @param {Object} [options] A dictionary object that allows for setting
       *     attributes via object members of the same name
       * @param {*} [options.data=null] The message content
       */
      constructor(type, options = {}) {
        super(type);
        this[kData] = options.data === void 0 ? null : options.data;
      }
      /**
       * @type {*}
       */
      get data() {
        return this[kData];
      }
    };
    Object.defineProperty(MessageEvent.prototype, "data", { enumerable: true });
    var EventTarget = {
      /**
       * Register an event listener.
       *
       * @param {String} type A string representing the event type to listen for
       * @param {(Function|Object)} handler The listener to add
       * @param {Object} [options] An options object specifies characteristics about
       *     the event listener
       * @param {Boolean} [options.once=false] A `Boolean` indicating that the
       *     listener should be invoked at most once after being added. If `true`,
       *     the listener would be automatically removed when invoked.
       * @public
       */
      addEventListener(type, handler, options = {}) {
        for (const listener of this.listeners(type)) {
          if (!options[kForOnEventAttribute] && listener[kListener] === handler && !listener[kForOnEventAttribute]) {
            return;
          }
        }
        let wrapper;
        if (type === "message") {
          wrapper = function onMessage(data, isBinary) {
            const event = new MessageEvent("message", {
              data: isBinary ? data : data.toString()
            });
            event[kTarget] = this;
            callListener(handler, this, event);
          };
        } else if (type === "close") {
          wrapper = function onClose(code, message) {
            const event = new CloseEvent("close", {
              code,
              reason: message.toString(),
              wasClean: this._closeFrameReceived && this._closeFrameSent
            });
            event[kTarget] = this;
            callListener(handler, this, event);
          };
        } else if (type === "error") {
          wrapper = function onError(error) {
            const event = new ErrorEvent("error", {
              error,
              message: error.message
            });
            event[kTarget] = this;
            callListener(handler, this, event);
          };
        } else if (type === "open") {
          wrapper = function onOpen() {
            const event = new Event("open");
            event[kTarget] = this;
            callListener(handler, this, event);
          };
        } else {
          return;
        }
        wrapper[kForOnEventAttribute] = !!options[kForOnEventAttribute];
        wrapper[kListener] = handler;
        if (options.once) {
          this.once(type, wrapper);
        } else {
          this.on(type, wrapper);
        }
      },
      /**
       * Remove an event listener.
       *
       * @param {String} type A string representing the event type to remove
       * @param {(Function|Object)} handler The listener to remove
       * @public
       */
      removeEventListener(type, handler) {
        for (const listener of this.listeners(type)) {
          if (listener[kListener] === handler && !listener[kForOnEventAttribute]) {
            this.removeListener(type, listener);
            break;
          }
        }
      }
    };
    module.exports = {
      CloseEvent,
      ErrorEvent,
      Event,
      EventTarget,
      MessageEvent
    };
    function callListener(listener, thisArg, event) {
      if (typeof listener === "object" && listener.handleEvent) {
        listener.handleEvent.call(listener, event);
      } else {
        listener.call(thisArg, event);
      }
    }
  }
});

// node_modules/ws/lib/extension.js
var require_extension = __commonJS({
  "node_modules/ws/lib/extension.js"(exports, module) {
    "use strict";
    var { tokenChars } = require_validation();
    function push(dest, name, elem) {
      if (dest[name] === void 0) dest[name] = [elem];
      else dest[name].push(elem);
    }
    function parse(header) {
      const offers = /* @__PURE__ */ Object.create(null);
      let params = /* @__PURE__ */ Object.create(null);
      let mustUnescape = false;
      let isEscaping = false;
      let inQuotes = false;
      let extensionName;
      let paramName;
      let start = -1;
      let code = -1;
      let end = -1;
      let i = 0;
      for (; i < header.length; i++) {
        code = header.charCodeAt(i);
        if (extensionName === void 0) {
          if (end === -1 && tokenChars[code] === 1) {
            if (start === -1) start = i;
          } else if (i !== 0 && (code === 32 || code === 9)) {
            if (end === -1 && start !== -1) end = i;
          } else if (code === 59 || code === 44) {
            if (start === -1) {
              throw new SyntaxError(`Unexpected character at index ${i}`);
            }
            if (end === -1) end = i;
            const name = header.slice(start, end);
            if (code === 44) {
              push(offers, name, params);
              params = /* @__PURE__ */ Object.create(null);
            } else {
              extensionName = name;
            }
            start = end = -1;
          } else {
            throw new SyntaxError(`Unexpected character at index ${i}`);
          }
        } else if (paramName === void 0) {
          if (end === -1 && tokenChars[code] === 1) {
            if (start === -1) start = i;
          } else if (code === 32 || code === 9) {
            if (end === -1 && start !== -1) end = i;
          } else if (code === 59 || code === 44) {
            if (start === -1) {
              throw new SyntaxError(`Unexpected character at index ${i}`);
            }
            if (end === -1) end = i;
            push(params, header.slice(start, end), true);
            if (code === 44) {
              push(offers, extensionName, params);
              params = /* @__PURE__ */ Object.create(null);
              extensionName = void 0;
            }
            start = end = -1;
          } else if (code === 61 && start !== -1 && end === -1) {
            paramName = header.slice(start, i);
            start = end = -1;
          } else {
            throw new SyntaxError(`Unexpected character at index ${i}`);
          }
        } else {
          if (isEscaping) {
            if (tokenChars[code] !== 1) {
              throw new SyntaxError(`Unexpected character at index ${i}`);
            }
            if (start === -1) start = i;
            else if (!mustUnescape) mustUnescape = true;
            isEscaping = false;
          } else if (inQuotes) {
            if (tokenChars[code] === 1) {
              if (start === -1) start = i;
            } else if (code === 34 && start !== -1) {
              inQuotes = false;
              end = i;
            } else if (code === 92) {
              isEscaping = true;
            } else {
              throw new SyntaxError(`Unexpected character at index ${i}`);
            }
          } else if (code === 34 && header.charCodeAt(i - 1) === 61) {
            inQuotes = true;
          } else if (end === -1 && tokenChars[code] === 1) {
            if (start === -1) start = i;
          } else if (start !== -1 && (code === 32 || code === 9)) {
            if (end === -1) end = i;
          } else if (code === 59 || code === 44) {
            if (start === -1) {
              throw new SyntaxError(`Unexpected character at index ${i}`);
            }
            if (end === -1) end = i;
            let value = header.slice(start, end);
            if (mustUnescape) {
              value = value.replace(/\\/g, "");
              mustUnescape = false;
            }
            push(params, paramName, value);
            if (code === 44) {
              push(offers, extensionName, params);
              params = /* @__PURE__ */ Object.create(null);
              extensionName = void 0;
            }
            paramName = void 0;
            start = end = -1;
          } else {
            throw new SyntaxError(`Unexpected character at index ${i}`);
          }
        }
      }
      if (start === -1 || inQuotes || code === 32 || code === 9) {
        throw new SyntaxError("Unexpected end of input");
      }
      if (end === -1) end = i;
      const token = header.slice(start, end);
      if (extensionName === void 0) {
        push(offers, token, params);
      } else {
        if (paramName === void 0) {
          push(params, token, true);
        } else if (mustUnescape) {
          push(params, paramName, token.replace(/\\/g, ""));
        } else {
          push(params, paramName, token);
        }
        push(offers, extensionName, params);
      }
      return offers;
    }
    function format(extensions) {
      return Object.keys(extensions).map((extension2) => {
        let configurations = extensions[extension2];
        if (!Array.isArray(configurations)) configurations = [configurations];
        return configurations.map((params) => {
          return [extension2].concat(
            Object.keys(params).map((k) => {
              let values = params[k];
              if (!Array.isArray(values)) values = [values];
              return values.map((v) => v === true ? k : `${k}=${v}`).join("; ");
            })
          ).join("; ");
        }).join(", ");
      }).join(", ");
    }
    module.exports = { format, parse };
  }
});

// node_modules/ws/lib/websocket.js
var require_websocket = __commonJS({
  "node_modules/ws/lib/websocket.js"(exports, module) {
    "use strict";
    var EventEmitter = __require("events");
    var https = __require("https");
    var http = __require("http");
    var net = __require("net");
    var tls = __require("tls");
    var { randomBytes, createHash: createHash2 } = __require("crypto");
    var { Duplex, Readable } = __require("stream");
    var { URL: URL2 } = __require("url");
    var PerMessageDeflate2 = require_permessage_deflate();
    var Receiver2 = require_receiver();
    var Sender2 = require_sender();
    var { isBlob } = require_validation();
    var {
      BINARY_TYPES,
      CLOSE_TIMEOUT,
      EMPTY_BUFFER,
      GUID,
      kForOnEventAttribute,
      kListener,
      kStatusCode,
      kWebSocket,
      NOOP
    } = require_constants();
    var {
      EventTarget: { addEventListener, removeEventListener }
    } = require_event_target();
    var { format, parse } = require_extension();
    var { toBuffer } = require_buffer_util();
    var kAborted = /* @__PURE__ */ Symbol("kAborted");
    var protocolVersions = [8, 13];
    var readyStates = ["CONNECTING", "OPEN", "CLOSING", "CLOSED"];
    var subprotocolRegex = /^[!#$%&'*+\-.0-9A-Z^_`|a-z~]+$/;
    var WebSocket2 = class _WebSocket extends EventEmitter {
      /**
       * Create a new `WebSocket`.
       *
       * @param {(String|URL)} address The URL to which to connect
       * @param {(String|String[])} [protocols] The subprotocols
       * @param {Object} [options] Connection options
       */
      constructor(address, protocols, options) {
        super();
        this._binaryType = BINARY_TYPES[0];
        this._closeCode = 1006;
        this._closeFrameReceived = false;
        this._closeFrameSent = false;
        this._closeMessage = EMPTY_BUFFER;
        this._closeTimer = null;
        this._errorEmitted = false;
        this._extensions = {};
        this._paused = false;
        this._protocol = "";
        this._readyState = _WebSocket.CONNECTING;
        this._receiver = null;
        this._sender = null;
        this._socket = null;
        if (address !== null) {
          this._bufferedAmount = 0;
          this._isServer = false;
          this._redirects = 0;
          if (protocols === void 0) {
            protocols = [];
          } else if (!Array.isArray(protocols)) {
            if (typeof protocols === "object" && protocols !== null) {
              options = protocols;
              protocols = [];
            } else {
              protocols = [protocols];
            }
          }
          initAsClient(this, address, protocols, options);
        } else {
          this._autoPong = options.autoPong;
          this._closeTimeout = options.closeTimeout;
          this._isServer = true;
        }
      }
      /**
       * For historical reasons, the custom "nodebuffer" type is used by the default
       * instead of "blob".
       *
       * @type {String}
       */
      get binaryType() {
        return this._binaryType;
      }
      set binaryType(type) {
        if (!BINARY_TYPES.includes(type)) return;
        this._binaryType = type;
        if (this._receiver) this._receiver._binaryType = type;
      }
      /**
       * @type {Number}
       */
      get bufferedAmount() {
        if (!this._socket) return this._bufferedAmount;
        return this._socket._writableState.length + this._sender._bufferedBytes;
      }
      /**
       * @type {String}
       */
      get extensions() {
        return Object.keys(this._extensions).join();
      }
      /**
       * @type {Boolean}
       */
      get isPaused() {
        return this._paused;
      }
      /**
       * @type {Function}
       */
      /* istanbul ignore next */
      get onclose() {
        return null;
      }
      /**
       * @type {Function}
       */
      /* istanbul ignore next */
      get onerror() {
        return null;
      }
      /**
       * @type {Function}
       */
      /* istanbul ignore next */
      get onopen() {
        return null;
      }
      /**
       * @type {Function}
       */
      /* istanbul ignore next */
      get onmessage() {
        return null;
      }
      /**
       * @type {String}
       */
      get protocol() {
        return this._protocol;
      }
      /**
       * @type {Number}
       */
      get readyState() {
        return this._readyState;
      }
      /**
       * @type {String}
       */
      get url() {
        return this._url;
      }
      /**
       * Set up the socket and the internal resources.
       *
       * @param {Duplex} socket The network socket between the server and client
       * @param {Buffer} head The first packet of the upgraded stream
       * @param {Object} options Options object
       * @param {Boolean} [options.allowSynchronousEvents=false] Specifies whether
       *     any of the `'message'`, `'ping'`, and `'pong'` events can be emitted
       *     multiple times in the same tick
       * @param {Function} [options.generateMask] The function used to generate the
       *     masking key
       * @param {Number} [options.maxBufferedChunks=0] The maximum number of
       *     buffered data chunks
       * @param {Number} [options.maxFragments=0] The maximum number of message
       *     fragments
       * @param {Number} [options.maxPayload=0] The maximum allowed message size
       * @param {Boolean} [options.skipUTF8Validation=false] Specifies whether or
       *     not to skip UTF-8 validation for text and close messages
       * @private
       */
      setSocket(socket2, head, options) {
        const receiver = new Receiver2({
          allowSynchronousEvents: options.allowSynchronousEvents,
          binaryType: this.binaryType,
          extensions: this._extensions,
          isServer: this._isServer,
          maxBufferedChunks: options.maxBufferedChunks,
          maxFragments: options.maxFragments,
          maxPayload: options.maxPayload,
          skipUTF8Validation: options.skipUTF8Validation
        });
        const sender = new Sender2(socket2, this._extensions, options.generateMask);
        this._receiver = receiver;
        this._sender = sender;
        this._socket = socket2;
        receiver[kWebSocket] = this;
        sender[kWebSocket] = this;
        socket2[kWebSocket] = this;
        receiver.on("conclude", receiverOnConclude);
        receiver.on("drain", receiverOnDrain);
        receiver.on("error", receiverOnError);
        receiver.on("message", receiverOnMessage);
        receiver.on("ping", receiverOnPing);
        receiver.on("pong", receiverOnPong);
        sender.onerror = senderOnError;
        if (socket2.setTimeout) socket2.setTimeout(0);
        if (socket2.setNoDelay) socket2.setNoDelay();
        if (head.length > 0) socket2.unshift(head);
        socket2.on("close", socketOnClose);
        socket2.on("data", socketOnData);
        socket2.on("end", socketOnEnd);
        socket2.on("error", socketOnError);
        this._readyState = _WebSocket.OPEN;
        this.emit("open");
      }
      /**
       * Emit the `'close'` event.
       *
       * @private
       */
      emitClose() {
        if (!this._socket) {
          this._readyState = _WebSocket.CLOSED;
          this.emit("close", this._closeCode, this._closeMessage);
          return;
        }
        if (this._extensions[PerMessageDeflate2.extensionName]) {
          this._extensions[PerMessageDeflate2.extensionName].cleanup();
        }
        this._receiver.removeAllListeners();
        this._readyState = _WebSocket.CLOSED;
        this.emit("close", this._closeCode, this._closeMessage);
      }
      /**
       * Start a closing handshake.
       *
       *          +----------+   +-----------+   +----------+
       *     - - -|ws.close()|-->|close frame|-->|ws.close()|- - -
       *    |     +----------+   +-----------+   +----------+     |
       *          +----------+   +-----------+         |
       * CLOSING  |ws.close()|<--|close frame|<--+-----+       CLOSING
       *          +----------+   +-----------+   |
       *    |           |                        |   +---+        |
       *                +------------------------+-->|fin| - - - -
       *    |         +---+                      |   +---+
       *     - - - - -|fin|<---------------------+
       *              +---+
       *
       * @param {Number} [code] Status code explaining why the connection is closing
       * @param {(String|Buffer)} [data] The reason why the connection is
       *     closing
       * @public
       */
      close(code, data) {
        if (this.readyState === _WebSocket.CLOSED) return;
        if (this.readyState === _WebSocket.CONNECTING) {
          const msg = "WebSocket was closed before the connection was established";
          abortHandshake(this, this._req, msg);
          return;
        }
        if (this.readyState === _WebSocket.CLOSING) {
          if (this._closeFrameSent && (this._closeFrameReceived || this._receiver._writableState.errorEmitted)) {
            this._socket.end();
          }
          return;
        }
        this._readyState = _WebSocket.CLOSING;
        this._sender.close(code, data, !this._isServer, (err) => {
          if (err) return;
          this._closeFrameSent = true;
          if (this._closeFrameReceived || this._receiver._writableState.errorEmitted) {
            this._socket.end();
          }
        });
        setCloseTimer(this);
      }
      /**
       * Pause the socket.
       *
       * @public
       */
      pause() {
        if (this.readyState === _WebSocket.CONNECTING || this.readyState === _WebSocket.CLOSED) {
          return;
        }
        this._paused = true;
        this._socket.pause();
      }
      /**
       * Send a ping.
       *
       * @param {*} [data] The data to send
       * @param {Boolean} [mask] Indicates whether or not to mask `data`
       * @param {Function} [cb] Callback which is executed when the ping is sent
       * @public
       */
      ping(data, mask, cb) {
        if (this.readyState === _WebSocket.CONNECTING) {
          throw new Error("WebSocket is not open: readyState 0 (CONNECTING)");
        }
        if (typeof data === "function") {
          cb = data;
          data = mask = void 0;
        } else if (typeof mask === "function") {
          cb = mask;
          mask = void 0;
        }
        if (typeof data === "number") data = data.toString();
        if (this.readyState !== _WebSocket.OPEN) {
          sendAfterClose(this, data, cb);
          return;
        }
        if (mask === void 0) mask = !this._isServer;
        this._sender.ping(data || EMPTY_BUFFER, mask, cb);
      }
      /**
       * Send a pong.
       *
       * @param {*} [data] The data to send
       * @param {Boolean} [mask] Indicates whether or not to mask `data`
       * @param {Function} [cb] Callback which is executed when the pong is sent
       * @public
       */
      pong(data, mask, cb) {
        if (this.readyState === _WebSocket.CONNECTING) {
          throw new Error("WebSocket is not open: readyState 0 (CONNECTING)");
        }
        if (typeof data === "function") {
          cb = data;
          data = mask = void 0;
        } else if (typeof mask === "function") {
          cb = mask;
          mask = void 0;
        }
        if (typeof data === "number") data = data.toString();
        if (this.readyState !== _WebSocket.OPEN) {
          sendAfterClose(this, data, cb);
          return;
        }
        if (mask === void 0) mask = !this._isServer;
        this._sender.pong(data || EMPTY_BUFFER, mask, cb);
      }
      /**
       * Resume the socket.
       *
       * @public
       */
      resume() {
        if (this.readyState === _WebSocket.CONNECTING || this.readyState === _WebSocket.CLOSED) {
          return;
        }
        this._paused = false;
        if (!this._receiver._writableState.needDrain) this._socket.resume();
      }
      /**
       * Send a data message.
       *
       * @param {*} data The message to send
       * @param {Object} [options] Options object
       * @param {Boolean} [options.binary] Specifies whether `data` is binary or
       *     text
       * @param {Boolean} [options.compress] Specifies whether or not to compress
       *     `data`
       * @param {Boolean} [options.fin=true] Specifies whether the fragment is the
       *     last one
       * @param {Boolean} [options.mask] Specifies whether or not to mask `data`
       * @param {Function} [cb] Callback which is executed when data is written out
       * @public
       */
      send(data, options, cb) {
        if (this.readyState === _WebSocket.CONNECTING) {
          throw new Error("WebSocket is not open: readyState 0 (CONNECTING)");
        }
        if (typeof options === "function") {
          cb = options;
          options = {};
        }
        if (typeof data === "number") data = data.toString();
        if (this.readyState !== _WebSocket.OPEN) {
          sendAfterClose(this, data, cb);
          return;
        }
        const opts = {
          binary: typeof data !== "string",
          mask: !this._isServer,
          compress: true,
          fin: true,
          ...options
        };
        if (!this._extensions[PerMessageDeflate2.extensionName]) {
          opts.compress = false;
        }
        this._sender.send(data || EMPTY_BUFFER, opts, cb);
      }
      /**
       * Forcibly close the connection.
       *
       * @public
       */
      terminate() {
        if (this.readyState === _WebSocket.CLOSED) return;
        if (this.readyState === _WebSocket.CONNECTING) {
          const msg = "WebSocket was closed before the connection was established";
          abortHandshake(this, this._req, msg);
          return;
        }
        if (this._socket) {
          this._readyState = _WebSocket.CLOSING;
          this._socket.destroy();
        }
      }
    };
    Object.defineProperty(WebSocket2, "CONNECTING", {
      enumerable: true,
      value: readyStates.indexOf("CONNECTING")
    });
    Object.defineProperty(WebSocket2.prototype, "CONNECTING", {
      enumerable: true,
      value: readyStates.indexOf("CONNECTING")
    });
    Object.defineProperty(WebSocket2, "OPEN", {
      enumerable: true,
      value: readyStates.indexOf("OPEN")
    });
    Object.defineProperty(WebSocket2.prototype, "OPEN", {
      enumerable: true,
      value: readyStates.indexOf("OPEN")
    });
    Object.defineProperty(WebSocket2, "CLOSING", {
      enumerable: true,
      value: readyStates.indexOf("CLOSING")
    });
    Object.defineProperty(WebSocket2.prototype, "CLOSING", {
      enumerable: true,
      value: readyStates.indexOf("CLOSING")
    });
    Object.defineProperty(WebSocket2, "CLOSED", {
      enumerable: true,
      value: readyStates.indexOf("CLOSED")
    });
    Object.defineProperty(WebSocket2.prototype, "CLOSED", {
      enumerable: true,
      value: readyStates.indexOf("CLOSED")
    });
    [
      "binaryType",
      "bufferedAmount",
      "extensions",
      "isPaused",
      "protocol",
      "readyState",
      "url"
    ].forEach((property) => {
      Object.defineProperty(WebSocket2.prototype, property, { enumerable: true });
    });
    ["open", "error", "close", "message"].forEach((method) => {
      Object.defineProperty(WebSocket2.prototype, `on${method}`, {
        enumerable: true,
        get() {
          for (const listener of this.listeners(method)) {
            if (listener[kForOnEventAttribute]) return listener[kListener];
          }
          return null;
        },
        set(handler) {
          for (const listener of this.listeners(method)) {
            if (listener[kForOnEventAttribute]) {
              this.removeListener(method, listener);
              break;
            }
          }
          if (typeof handler !== "function") return;
          this.addEventListener(method, handler, {
            [kForOnEventAttribute]: true
          });
        }
      });
    });
    WebSocket2.prototype.addEventListener = addEventListener;
    WebSocket2.prototype.removeEventListener = removeEventListener;
    module.exports = WebSocket2;
    function initAsClient(websocket, address, protocols, options) {
      const opts = {
        allowSynchronousEvents: true,
        autoPong: true,
        closeTimeout: CLOSE_TIMEOUT,
        protocolVersion: protocolVersions[1],
        maxBufferedChunks: 256 * 1024,
        maxFragments: 16 * 1024,
        maxPayload: 100 * 1024 * 1024,
        skipUTF8Validation: false,
        perMessageDeflate: true,
        followRedirects: false,
        maxRedirects: 10,
        ...options,
        socketPath: void 0,
        hostname: void 0,
        protocol: void 0,
        timeout: void 0,
        method: "GET",
        host: void 0,
        path: void 0,
        port: void 0
      };
      websocket._autoPong = opts.autoPong;
      websocket._closeTimeout = opts.closeTimeout;
      if (!protocolVersions.includes(opts.protocolVersion)) {
        throw new RangeError(
          `Unsupported protocol version: ${opts.protocolVersion} (supported versions: ${protocolVersions.join(", ")})`
        );
      }
      let parsedUrl;
      if (address instanceof URL2) {
        parsedUrl = address;
      } else {
        try {
          parsedUrl = new URL2(address);
        } catch {
          throw new SyntaxError(`Invalid URL: ${address}`);
        }
      }
      if (parsedUrl.protocol === "http:") {
        parsedUrl.protocol = "ws:";
      } else if (parsedUrl.protocol === "https:") {
        parsedUrl.protocol = "wss:";
      }
      websocket._url = parsedUrl.href;
      const isSecure = parsedUrl.protocol === "wss:";
      const isIpcUrl = parsedUrl.protocol === "ws+unix:";
      let invalidUrlMessage;
      if (parsedUrl.protocol !== "ws:" && !isSecure && !isIpcUrl) {
        invalidUrlMessage = `The URL's protocol must be one of "ws:", "wss:", "http:", "https:", or "ws+unix:"`;
      } else if (isIpcUrl && !parsedUrl.pathname) {
        invalidUrlMessage = "The URL's pathname is empty";
      } else if (parsedUrl.hash) {
        invalidUrlMessage = "The URL contains a fragment identifier";
      }
      if (invalidUrlMessage) {
        const err = new SyntaxError(invalidUrlMessage);
        if (websocket._redirects === 0) {
          throw err;
        } else {
          emitErrorAndClose(websocket, err);
          return;
        }
      }
      const defaultPort = isSecure ? 443 : 80;
      const key = randomBytes(16).toString("base64");
      const request = isSecure ? https.request : http.request;
      const protocolSet = /* @__PURE__ */ new Set();
      let perMessageDeflate;
      opts.createConnection = opts.createConnection || (isSecure ? tlsConnect : netConnect);
      opts.defaultPort = opts.defaultPort || defaultPort;
      opts.port = parsedUrl.port || defaultPort;
      opts.host = parsedUrl.hostname.startsWith("[") ? parsedUrl.hostname.slice(1, -1) : parsedUrl.hostname;
      opts.headers = {
        ...opts.headers,
        "Sec-WebSocket-Version": opts.protocolVersion,
        "Sec-WebSocket-Key": key,
        Connection: "Upgrade",
        Upgrade: "websocket"
      };
      opts.path = parsedUrl.pathname + parsedUrl.search;
      opts.timeout = opts.handshakeTimeout;
      if (opts.perMessageDeflate) {
        perMessageDeflate = new PerMessageDeflate2({
          ...opts.perMessageDeflate,
          isServer: false,
          maxPayload: opts.maxPayload
        });
        opts.headers["Sec-WebSocket-Extensions"] = format({
          [PerMessageDeflate2.extensionName]: perMessageDeflate.offer()
        });
      }
      if (protocols.length) {
        for (const protocol of protocols) {
          if (typeof protocol !== "string" || !subprotocolRegex.test(protocol) || protocolSet.has(protocol)) {
            throw new SyntaxError(
              "An invalid or duplicated subprotocol was specified"
            );
          }
          protocolSet.add(protocol);
        }
        opts.headers["Sec-WebSocket-Protocol"] = protocols.join(",");
      }
      if (opts.origin) {
        if (opts.protocolVersion < 13) {
          opts.headers["Sec-WebSocket-Origin"] = opts.origin;
        } else {
          opts.headers.Origin = opts.origin;
        }
      }
      if (parsedUrl.username || parsedUrl.password) {
        opts.auth = `${parsedUrl.username}:${parsedUrl.password}`;
      }
      if (isIpcUrl) {
        const parts = opts.path.split(":");
        opts.socketPath = parts[0];
        opts.path = parts[1];
      }
      let req;
      if (opts.followRedirects) {
        if (websocket._redirects === 0) {
          websocket._originalIpc = isIpcUrl;
          websocket._originalSecure = isSecure;
          websocket._originalHostOrSocketPath = isIpcUrl ? opts.socketPath : parsedUrl.host;
          const headers = options && options.headers;
          options = { ...options, headers: {} };
          if (headers) {
            for (const [key2, value] of Object.entries(headers)) {
              options.headers[key2.toLowerCase()] = value;
            }
          }
        } else if (websocket.listenerCount("redirect") === 0) {
          const isSameHost = isIpcUrl ? websocket._originalIpc ? opts.socketPath === websocket._originalHostOrSocketPath : false : websocket._originalIpc ? false : parsedUrl.host === websocket._originalHostOrSocketPath;
          if (!isSameHost || websocket._originalSecure && !isSecure) {
            delete opts.headers.authorization;
            delete opts.headers.cookie;
            if (!isSameHost) delete opts.headers.host;
            opts.auth = void 0;
          }
        }
        if (opts.auth && !options.headers.authorization) {
          options.headers.authorization = "Basic " + Buffer.from(opts.auth).toString("base64");
        }
        req = websocket._req = request(opts);
        if (websocket._redirects) {
          websocket.emit("redirect", websocket.url, req);
        }
      } else {
        req = websocket._req = request(opts);
      }
      if (opts.timeout) {
        req.on("timeout", () => {
          abortHandshake(websocket, req, "Opening handshake has timed out");
        });
      }
      req.on("error", (err) => {
        if (req === null || req[kAborted]) return;
        req = websocket._req = null;
        emitErrorAndClose(websocket, err);
      });
      req.on("response", (res) => {
        const location = res.headers.location;
        const statusCode = res.statusCode;
        if (location && opts.followRedirects && statusCode >= 300 && statusCode < 400) {
          if (++websocket._redirects > opts.maxRedirects) {
            abortHandshake(websocket, req, "Maximum redirects exceeded");
            return;
          }
          req.abort();
          let addr;
          try {
            addr = new URL2(location, address);
          } catch (e) {
            const err = new SyntaxError(`Invalid URL: ${location}`);
            emitErrorAndClose(websocket, err);
            return;
          }
          initAsClient(websocket, addr, protocols, options);
        } else if (!websocket.emit("unexpected-response", req, res)) {
          abortHandshake(
            websocket,
            req,
            `Unexpected server response: ${res.statusCode}`
          );
        }
      });
      req.on("upgrade", (res, socket2, head) => {
        websocket.emit("upgrade", res);
        if (websocket.readyState !== WebSocket2.CONNECTING) return;
        req = websocket._req = null;
        const upgrade = res.headers.upgrade;
        if (upgrade === void 0 || upgrade.toLowerCase() !== "websocket") {
          abortHandshake(websocket, socket2, "Invalid Upgrade header");
          return;
        }
        const digest = createHash2("sha1").update(key + GUID).digest("base64");
        if (res.headers["sec-websocket-accept"] !== digest) {
          abortHandshake(websocket, socket2, "Invalid Sec-WebSocket-Accept header");
          return;
        }
        const serverProt = res.headers["sec-websocket-protocol"];
        let protError;
        if (serverProt !== void 0) {
          if (!protocolSet.size) {
            protError = "Server sent a subprotocol but none was requested";
          } else if (!protocolSet.has(serverProt)) {
            protError = "Server sent an invalid subprotocol";
          }
        } else if (protocolSet.size) {
          protError = "Server sent no subprotocol";
        }
        if (protError) {
          abortHandshake(websocket, socket2, protError);
          return;
        }
        if (serverProt) websocket._protocol = serverProt;
        const secWebSocketExtensions = res.headers["sec-websocket-extensions"];
        if (secWebSocketExtensions !== void 0) {
          if (!perMessageDeflate) {
            const message = "Server sent a Sec-WebSocket-Extensions header but no extension was requested";
            abortHandshake(websocket, socket2, message);
            return;
          }
          let extensions;
          try {
            extensions = parse(secWebSocketExtensions);
          } catch (err) {
            const message = "Invalid Sec-WebSocket-Extensions header";
            abortHandshake(websocket, socket2, message);
            return;
          }
          const extensionNames = Object.keys(extensions);
          if (extensionNames.length !== 1 || extensionNames[0] !== PerMessageDeflate2.extensionName) {
            const message = "Server indicated an extension that was not requested";
            abortHandshake(websocket, socket2, message);
            return;
          }
          try {
            perMessageDeflate.accept(extensions[PerMessageDeflate2.extensionName]);
          } catch (err) {
            const message = "Invalid Sec-WebSocket-Extensions header";
            abortHandshake(websocket, socket2, message);
            return;
          }
          websocket._extensions[PerMessageDeflate2.extensionName] = perMessageDeflate;
        }
        websocket.setSocket(socket2, head, {
          allowSynchronousEvents: opts.allowSynchronousEvents,
          generateMask: opts.generateMask,
          maxBufferedChunks: opts.maxBufferedChunks,
          maxFragments: opts.maxFragments,
          maxPayload: opts.maxPayload,
          skipUTF8Validation: opts.skipUTF8Validation
        });
      });
      if (opts.finishRequest) {
        opts.finishRequest(req, websocket);
      } else {
        req.end();
      }
    }
    function emitErrorAndClose(websocket, err) {
      websocket._readyState = WebSocket2.CLOSING;
      websocket._errorEmitted = true;
      websocket.emit("error", err);
      websocket.emitClose();
    }
    function netConnect(options) {
      options.path = options.socketPath;
      return net.connect(options);
    }
    function tlsConnect(options) {
      options.path = void 0;
      if (!options.servername && options.servername !== "") {
        options.servername = net.isIP(options.host) ? "" : options.host;
      }
      return tls.connect(options);
    }
    function abortHandshake(websocket, stream, message) {
      websocket._readyState = WebSocket2.CLOSING;
      const err = new Error(message);
      Error.captureStackTrace(err, abortHandshake);
      if (stream.setHeader) {
        stream[kAborted] = true;
        stream.abort();
        if (stream.socket && !stream.socket.destroyed) {
          stream.socket.destroy();
        }
        process.nextTick(emitErrorAndClose, websocket, err);
      } else {
        stream.destroy(err);
        stream.once("error", websocket.emit.bind(websocket, "error"));
        stream.once("close", websocket.emitClose.bind(websocket));
      }
    }
    function sendAfterClose(websocket, data, cb) {
      if (data) {
        const length = isBlob(data) ? data.size : toBuffer(data).length;
        if (websocket._socket) websocket._sender._bufferedBytes += length;
        else websocket._bufferedAmount += length;
      }
      if (cb) {
        const err = new Error(
          `WebSocket is not open: readyState ${websocket.readyState} (${readyStates[websocket.readyState]})`
        );
        process.nextTick(cb, err);
      }
    }
    function receiverOnConclude(code, reason) {
      const websocket = this[kWebSocket];
      websocket._closeFrameReceived = true;
      websocket._closeMessage = reason;
      websocket._closeCode = code;
      if (websocket._socket[kWebSocket] === void 0) return;
      websocket._socket.removeListener("data", socketOnData);
      process.nextTick(resume, websocket._socket);
      if (code === 1005) websocket.close();
      else websocket.close(code, reason);
    }
    function receiverOnDrain() {
      const websocket = this[kWebSocket];
      if (!websocket.isPaused) websocket._socket.resume();
    }
    function receiverOnError(err) {
      const websocket = this[kWebSocket];
      if (websocket._socket[kWebSocket] !== void 0) {
        websocket._socket.removeListener("data", socketOnData);
        process.nextTick(resume, websocket._socket);
        websocket.close(err[kStatusCode]);
      }
      if (!websocket._errorEmitted) {
        websocket._errorEmitted = true;
        websocket.emit("error", err);
      }
    }
    function receiverOnFinish() {
      this[kWebSocket].emitClose();
    }
    function receiverOnMessage(data, isBinary) {
      this[kWebSocket].emit("message", data, isBinary);
    }
    function receiverOnPing(data) {
      const websocket = this[kWebSocket];
      if (websocket._autoPong) websocket.pong(data, !this._isServer, NOOP);
      websocket.emit("ping", data);
    }
    function receiverOnPong(data) {
      this[kWebSocket].emit("pong", data);
    }
    function resume(stream) {
      stream.resume();
    }
    function senderOnError(err) {
      const websocket = this[kWebSocket];
      if (websocket.readyState === WebSocket2.CLOSED) return;
      if (websocket.readyState === WebSocket2.OPEN) {
        websocket._readyState = WebSocket2.CLOSING;
        setCloseTimer(websocket);
      }
      this._socket.end();
      if (!websocket._errorEmitted) {
        websocket._errorEmitted = true;
        websocket.emit("error", err);
      }
    }
    function setCloseTimer(websocket) {
      websocket._closeTimer = setTimeout(
        websocket._socket.destroy.bind(websocket._socket),
        websocket._closeTimeout
      );
    }
    function socketOnClose() {
      const websocket = this[kWebSocket];
      this.removeListener("close", socketOnClose);
      this.removeListener("data", socketOnData);
      this.removeListener("end", socketOnEnd);
      websocket._readyState = WebSocket2.CLOSING;
      if (!this._readableState.endEmitted && !websocket._closeFrameReceived && !websocket._receiver._writableState.errorEmitted && this._readableState.length !== 0) {
        const chunk = this.read(this._readableState.length);
        websocket._receiver.write(chunk);
      }
      websocket._receiver.end();
      this[kWebSocket] = void 0;
      clearTimeout(websocket._closeTimer);
      if (websocket._receiver._writableState.finished || websocket._receiver._writableState.errorEmitted) {
        websocket.emitClose();
      } else {
        websocket._receiver.on("error", receiverOnFinish);
        websocket._receiver.on("finish", receiverOnFinish);
      }
    }
    function socketOnData(chunk) {
      if (!this[kWebSocket]._receiver.write(chunk)) {
        this.pause();
      }
    }
    function socketOnEnd() {
      const websocket = this[kWebSocket];
      websocket._readyState = WebSocket2.CLOSING;
      websocket._receiver.end();
      this.end();
    }
    function socketOnError() {
      const websocket = this[kWebSocket];
      this.removeListener("error", socketOnError);
      this.on("error", NOOP);
      if (websocket) {
        websocket._readyState = WebSocket2.CLOSING;
        this.destroy();
      }
    }
  }
});

// node_modules/ws/lib/stream.js
var require_stream = __commonJS({
  "node_modules/ws/lib/stream.js"(exports, module) {
    "use strict";
    var WebSocket2 = require_websocket();
    var { Duplex } = __require("stream");
    function emitClose(stream) {
      stream.emit("close");
    }
    function duplexOnEnd() {
      if (!this.destroyed && this._writableState.finished) {
        this.destroy();
      }
    }
    function duplexOnError(err) {
      this.removeListener("error", duplexOnError);
      this.destroy();
      if (this.listenerCount("error") === 0) {
        this.emit("error", err);
      }
    }
    function createWebSocketStream2(ws, options) {
      let terminateOnDestroy = true;
      const duplex = new Duplex({
        ...options,
        autoDestroy: false,
        emitClose: false,
        objectMode: false,
        writableObjectMode: false
      });
      ws.on("message", function message(msg, isBinary) {
        const data = !isBinary && duplex._readableState.objectMode ? msg.toString() : msg;
        if (!duplex.push(data)) ws.pause();
      });
      ws.once("error", function error(err) {
        if (duplex.destroyed) return;
        terminateOnDestroy = false;
        duplex.destroy(err);
      });
      ws.once("close", function close() {
        if (duplex.destroyed) return;
        duplex.push(null);
      });
      duplex._destroy = function(err, callback) {
        if (ws.readyState === ws.CLOSED) {
          callback(err);
          process.nextTick(emitClose, duplex);
          return;
        }
        let called = false;
        ws.once("error", function error(err2) {
          called = true;
          callback(err2);
        });
        ws.once("close", function close() {
          if (!called) callback(err);
          process.nextTick(emitClose, duplex);
        });
        if (terminateOnDestroy) ws.terminate();
      };
      duplex._final = function(callback) {
        if (ws.readyState === ws.CONNECTING) {
          ws.once("open", function open() {
            duplex._final(callback);
          });
          return;
        }
        if (ws._socket === null) return;
        if (ws._socket._writableState.finished) {
          callback();
          if (duplex._readableState.endEmitted) duplex.destroy();
        } else {
          ws._socket.once("finish", function finish() {
            callback();
          });
          ws.close();
        }
      };
      duplex._read = function() {
        if (ws.isPaused) ws.resume();
      };
      duplex._write = function(chunk, encoding, callback) {
        if (ws.readyState === ws.CONNECTING) {
          ws.once("open", function open() {
            duplex._write(chunk, encoding, callback);
          });
          return;
        }
        ws.send(chunk, callback);
      };
      duplex.on("end", duplexOnEnd);
      duplex.on("error", duplexOnError);
      return duplex;
    }
    module.exports = createWebSocketStream2;
  }
});

// node_modules/ws/lib/subprotocol.js
var require_subprotocol = __commonJS({
  "node_modules/ws/lib/subprotocol.js"(exports, module) {
    "use strict";
    var { tokenChars } = require_validation();
    function parse(header) {
      const protocols = /* @__PURE__ */ new Set();
      let start = -1;
      let end = -1;
      let i = 0;
      for (i; i < header.length; i++) {
        const code = header.charCodeAt(i);
        if (end === -1 && tokenChars[code] === 1) {
          if (start === -1) start = i;
        } else if (i !== 0 && (code === 32 || code === 9)) {
          if (end === -1 && start !== -1) end = i;
        } else if (code === 44) {
          if (start === -1) {
            throw new SyntaxError(`Unexpected character at index ${i}`);
          }
          if (end === -1) end = i;
          const protocol2 = header.slice(start, end);
          if (protocols.has(protocol2)) {
            throw new SyntaxError(`The "${protocol2}" subprotocol is duplicated`);
          }
          protocols.add(protocol2);
          start = end = -1;
        } else {
          throw new SyntaxError(`Unexpected character at index ${i}`);
        }
      }
      if (start === -1 || end !== -1) {
        throw new SyntaxError("Unexpected end of input");
      }
      const protocol = header.slice(start, i);
      if (protocols.has(protocol)) {
        throw new SyntaxError(`The "${protocol}" subprotocol is duplicated`);
      }
      protocols.add(protocol);
      return protocols;
    }
    module.exports = { parse };
  }
});

// node_modules/ws/lib/websocket-server.js
var require_websocket_server = __commonJS({
  "node_modules/ws/lib/websocket-server.js"(exports, module) {
    "use strict";
    var EventEmitter = __require("events");
    var http = __require("http");
    var { Duplex } = __require("stream");
    var { createHash: createHash2 } = __require("crypto");
    var extension2 = require_extension();
    var PerMessageDeflate2 = require_permessage_deflate();
    var subprotocol2 = require_subprotocol();
    var WebSocket2 = require_websocket();
    var { CLOSE_TIMEOUT, GUID, kWebSocket } = require_constants();
    var keyRegex = /^[+/0-9A-Za-z]{22}==$/;
    var RUNNING = 0;
    var CLOSING = 1;
    var CLOSED = 2;
    var WebSocketServer2 = class extends EventEmitter {
      /**
       * Create a `WebSocketServer` instance.
       *
       * @param {Object} options Configuration options
       * @param {Boolean} [options.allowSynchronousEvents=true] Specifies whether
       *     any of the `'message'`, `'ping'`, and `'pong'` events can be emitted
       *     multiple times in the same tick
       * @param {Boolean} [options.autoPong=true] Specifies whether or not to
       *     automatically send a pong in response to a ping
       * @param {Number} [options.backlog=511] The maximum length of the queue of
       *     pending connections
       * @param {Boolean} [options.clientTracking=true] Specifies whether or not to
       *     track clients
       * @param {Number} [options.closeTimeout=30000] Duration in milliseconds to
       *     wait for the closing handshake to finish after `websocket.close()` is
       *     called
       * @param {Function} [options.handleProtocols] A hook to handle protocols
       * @param {String} [options.host] The hostname where to bind the server
       * @param {Number} [options.maxBufferedChunks=262144] The maximum number of
       *     buffered data chunks
       * @param {Number} [options.maxFragments=16384] The maximum number of message
       *     fragments
       * @param {Number} [options.maxPayload=104857600] The maximum allowed message
       *     size
       * @param {Boolean} [options.noServer=false] Enable no server mode
       * @param {String} [options.path] Accept only connections matching this path
       * @param {(Boolean|Object)} [options.perMessageDeflate=false] Enable/disable
       *     permessage-deflate
       * @param {Number} [options.port] The port where to bind the server
       * @param {(http.Server|https.Server)} [options.server] A pre-created HTTP/S
       *     server to use
       * @param {Boolean} [options.skipUTF8Validation=false] Specifies whether or
       *     not to skip UTF-8 validation for text and close messages
       * @param {Function} [options.verifyClient] A hook to reject connections
       * @param {Function} [options.WebSocket=WebSocket] Specifies the `WebSocket`
       *     class to use. It must be the `WebSocket` class or class that extends it
       * @param {Function} [callback] A listener for the `listening` event
       */
      constructor(options, callback) {
        super();
        options = {
          allowSynchronousEvents: true,
          autoPong: true,
          maxBufferedChunks: 256 * 1024,
          maxFragments: 16 * 1024,
          maxPayload: 100 * 1024 * 1024,
          skipUTF8Validation: false,
          perMessageDeflate: false,
          handleProtocols: null,
          clientTracking: true,
          closeTimeout: CLOSE_TIMEOUT,
          verifyClient: null,
          noServer: false,
          backlog: null,
          // use default (511 as implemented in net.js)
          server: null,
          host: null,
          path: null,
          port: null,
          WebSocket: WebSocket2,
          ...options
        };
        if (options.port == null && !options.server && !options.noServer || options.port != null && (options.server || options.noServer) || options.server && options.noServer) {
          throw new TypeError(
            'One and only one of the "port", "server", or "noServer" options must be specified'
          );
        }
        if (options.port != null) {
          this._server = http.createServer((req, res) => {
            const body = http.STATUS_CODES[426];
            res.writeHead(426, {
              "Content-Length": body.length,
              "Content-Type": "text/plain"
            });
            res.end(body);
          });
          this._server.listen(
            options.port,
            options.host,
            options.backlog,
            callback
          );
        } else if (options.server) {
          this._server = options.server;
        }
        if (this._server) {
          const emitConnection = this.emit.bind(this, "connection");
          this._removeListeners = addListeners(this._server, {
            listening: this.emit.bind(this, "listening"),
            error: this.emit.bind(this, "error"),
            upgrade: (req, socket2, head) => {
              this.handleUpgrade(req, socket2, head, emitConnection);
            }
          });
        }
        if (options.perMessageDeflate === true) options.perMessageDeflate = {};
        if (options.clientTracking) {
          this.clients = /* @__PURE__ */ new Set();
          this._shouldEmitClose = false;
        }
        this.options = options;
        this._state = RUNNING;
      }
      /**
       * Returns the bound address, the address family name, and port of the server
       * as reported by the operating system if listening on an IP socket.
       * If the server is listening on a pipe or UNIX domain socket, the name is
       * returned as a string.
       *
       * @return {(Object|String|null)} The address of the server
       * @public
       */
      address() {
        if (this.options.noServer) {
          throw new Error('The server is operating in "noServer" mode');
        }
        if (!this._server) return null;
        return this._server.address();
      }
      /**
       * Stop the server from accepting new connections and emit the `'close'` event
       * when all existing connections are closed.
       *
       * @param {Function} [cb] A one-time listener for the `'close'` event
       * @public
       */
      close(cb) {
        if (this._state === CLOSED) {
          if (cb) {
            this.once("close", () => {
              cb(new Error("The server is not running"));
            });
          }
          process.nextTick(emitClose, this);
          return;
        }
        if (cb) this.once("close", cb);
        if (this._state === CLOSING) return;
        this._state = CLOSING;
        if (this.options.noServer || this.options.server) {
          if (this._server) {
            this._removeListeners();
            this._removeListeners = this._server = null;
          }
          if (this.clients) {
            if (!this.clients.size) {
              process.nextTick(emitClose, this);
            } else {
              this._shouldEmitClose = true;
            }
          } else {
            process.nextTick(emitClose, this);
          }
        } else {
          const server = this._server;
          this._removeListeners();
          this._removeListeners = this._server = null;
          server.close(() => {
            emitClose(this);
          });
        }
      }
      /**
       * See if a given request should be handled by this server instance.
       *
       * @param {http.IncomingMessage} req Request object to inspect
       * @return {Boolean} `true` if the request is valid, else `false`
       * @public
       */
      shouldHandle(req) {
        if (this.options.path) {
          const index = req.url.indexOf("?");
          const pathname = index !== -1 ? req.url.slice(0, index) : req.url;
          if (pathname !== this.options.path) return false;
        }
        return true;
      }
      /**
       * Handle a HTTP Upgrade request.
       *
       * @param {http.IncomingMessage} req The request object
       * @param {Duplex} socket The network socket between the server and client
       * @param {Buffer} head The first packet of the upgraded stream
       * @param {Function} cb Callback
       * @public
       */
      handleUpgrade(req, socket2, head, cb) {
        socket2.on("error", socketOnError);
        const key = req.headers["sec-websocket-key"];
        const upgrade = req.headers.upgrade;
        const version = +req.headers["sec-websocket-version"];
        if (req.method !== "GET") {
          const message = "Invalid HTTP method";
          abortHandshakeOrEmitwsClientError(this, req, socket2, 405, message);
          return;
        }
        if (upgrade === void 0 || upgrade.toLowerCase() !== "websocket") {
          const message = "Invalid Upgrade header";
          abortHandshakeOrEmitwsClientError(this, req, socket2, 400, message);
          return;
        }
        if (key === void 0 || !keyRegex.test(key)) {
          const message = "Missing or invalid Sec-WebSocket-Key header";
          abortHandshakeOrEmitwsClientError(this, req, socket2, 400, message);
          return;
        }
        if (version !== 13 && version !== 8) {
          const message = "Missing or invalid Sec-WebSocket-Version header";
          abortHandshakeOrEmitwsClientError(this, req, socket2, 400, message, {
            "Sec-WebSocket-Version": "13, 8"
          });
          return;
        }
        if (!this.shouldHandle(req)) {
          abortHandshake(socket2, 400);
          return;
        }
        const secWebSocketProtocol = req.headers["sec-websocket-protocol"];
        let protocols = /* @__PURE__ */ new Set();
        if (secWebSocketProtocol !== void 0) {
          try {
            protocols = subprotocol2.parse(secWebSocketProtocol);
          } catch (err) {
            const message = "Invalid Sec-WebSocket-Protocol header";
            abortHandshakeOrEmitwsClientError(this, req, socket2, 400, message);
            return;
          }
        }
        const secWebSocketExtensions = req.headers["sec-websocket-extensions"];
        const extensions = {};
        if (this.options.perMessageDeflate && secWebSocketExtensions !== void 0) {
          const perMessageDeflate = new PerMessageDeflate2({
            ...this.options.perMessageDeflate,
            isServer: true,
            maxPayload: this.options.maxPayload
          });
          try {
            const offers = extension2.parse(secWebSocketExtensions);
            if (offers[PerMessageDeflate2.extensionName]) {
              perMessageDeflate.accept(offers[PerMessageDeflate2.extensionName]);
              extensions[PerMessageDeflate2.extensionName] = perMessageDeflate;
            }
          } catch (err) {
            const message = "Invalid or unacceptable Sec-WebSocket-Extensions header";
            abortHandshakeOrEmitwsClientError(this, req, socket2, 400, message);
            return;
          }
        }
        if (this.options.verifyClient) {
          const info = {
            origin: req.headers[`${version === 8 ? "sec-websocket-origin" : "origin"}`],
            secure: !!(req.socket.authorized || req.socket.encrypted),
            req
          };
          if (this.options.verifyClient.length === 2) {
            this.options.verifyClient(info, (verified, code, message, headers) => {
              if (!verified) {
                return abortHandshake(socket2, code || 401, message, headers);
              }
              this.completeUpgrade(
                extensions,
                key,
                protocols,
                req,
                socket2,
                head,
                cb
              );
            });
            return;
          }
          if (!this.options.verifyClient(info)) return abortHandshake(socket2, 401);
        }
        this.completeUpgrade(extensions, key, protocols, req, socket2, head, cb);
      }
      /**
       * Upgrade the connection to WebSocket.
       *
       * @param {Object} extensions The accepted extensions
       * @param {String} key The value of the `Sec-WebSocket-Key` header
       * @param {Set} protocols The subprotocols
       * @param {http.IncomingMessage} req The request object
       * @param {Duplex} socket The network socket between the server and client
       * @param {Buffer} head The first packet of the upgraded stream
       * @param {Function} cb Callback
       * @throws {Error} If called more than once with the same socket
       * @private
       */
      completeUpgrade(extensions, key, protocols, req, socket2, head, cb) {
        if (!socket2.readable || !socket2.writable) return socket2.destroy();
        if (socket2[kWebSocket]) {
          throw new Error(
            "server.handleUpgrade() was called more than once with the same socket, possibly due to a misconfiguration"
          );
        }
        if (this._state > RUNNING) return abortHandshake(socket2, 503);
        const digest = createHash2("sha1").update(key + GUID).digest("base64");
        const headers = [
          "HTTP/1.1 101 Switching Protocols",
          "Upgrade: websocket",
          "Connection: Upgrade",
          `Sec-WebSocket-Accept: ${digest}`
        ];
        const ws = new this.options.WebSocket(null, void 0, this.options);
        if (protocols.size) {
          const protocol = this.options.handleProtocols ? this.options.handleProtocols(protocols, req) : protocols.values().next().value;
          if (protocol) {
            headers.push(`Sec-WebSocket-Protocol: ${protocol}`);
            ws._protocol = protocol;
          }
        }
        if (extensions[PerMessageDeflate2.extensionName]) {
          const params = extensions[PerMessageDeflate2.extensionName].params;
          const value = extension2.format({
            [PerMessageDeflate2.extensionName]: [params]
          });
          headers.push(`Sec-WebSocket-Extensions: ${value}`);
          ws._extensions = extensions;
        }
        this.emit("headers", headers, req);
        socket2.write(headers.concat("\r\n").join("\r\n"));
        socket2.removeListener("error", socketOnError);
        ws.setSocket(socket2, head, {
          allowSynchronousEvents: this.options.allowSynchronousEvents,
          maxBufferedChunks: this.options.maxBufferedChunks,
          maxFragments: this.options.maxFragments,
          maxPayload: this.options.maxPayload,
          skipUTF8Validation: this.options.skipUTF8Validation
        });
        if (this.clients) {
          this.clients.add(ws);
          ws.on("close", () => {
            this.clients.delete(ws);
            if (this._shouldEmitClose && !this.clients.size) {
              process.nextTick(emitClose, this);
            }
          });
        }
        cb(ws, req);
      }
    };
    module.exports = WebSocketServer2;
    function addListeners(server, map) {
      for (const event of Object.keys(map)) server.on(event, map[event]);
      return function removeListeners() {
        for (const event of Object.keys(map)) {
          server.removeListener(event, map[event]);
        }
      };
    }
    function emitClose(server) {
      server._state = CLOSED;
      server.emit("close");
    }
    function socketOnError() {
      this.destroy();
    }
    function abortHandshake(socket2, code, message, headers) {
      message = message || http.STATUS_CODES[code];
      headers = {
        Connection: "close",
        "Content-Type": "text/html",
        "Content-Length": Buffer.byteLength(message),
        ...headers
      };
      socket2.once("finish", socket2.destroy);
      socket2.end(
        `HTTP/1.1 ${code} ${http.STATUS_CODES[code]}\r
` + Object.keys(headers).map((h) => `${h}: ${headers[h]}`).join("\r\n") + "\r\n\r\n" + message
      );
    }
    function abortHandshakeOrEmitwsClientError(server, req, socket2, code, message, headers) {
      if (server.listenerCount("wsClientError")) {
        const err = new Error(message);
        Error.captureStackTrace(err, abortHandshakeOrEmitwsClientError);
        server.emit("wsClientError", err, socket2, req);
      } else {
        abortHandshake(socket2, code, message, headers);
      }
    }
  }
});

// node_modules/@microsoft/agent-host-protocol/dist/types/common/errors.js
var JsonRpcErrorCodes = {
  /** Invalid JSON */
  ParseError: -32700,
  /** Not a valid JSON-RPC request */
  InvalidRequest: -32600,
  /** Unknown method name */
  MethodNotFound: -32601,
  /** Invalid method parameters */
  InvalidParams: -32602,
  /** Unspecified server error */
  InternalError: -32603
};

// node_modules/@microsoft/agent-host-protocol/dist/client/async-queue.js
var AsyncBroadcastQueue = class {
  buffer = [];
  /** Absolute logical position of `buffer[0]` (entries below have been dropped). */
  base = 0;
  cursors = /* @__PURE__ */ new Set();
  closed = false;
  bufferLimit;
  constructor(bufferLimit = 4096) {
    this.bufferLimit = bufferLimit;
  }
  /** Whether the queue has been closed. New readers see immediate end-of-stream. */
  get isClosed() {
    return this.closed;
  }
  /** Whether at least one reader is attached. */
  get hasReaders() {
    return this.cursors.size > 0;
  }
  /** Publish a value to every attached reader. */
  publish(value) {
    if (this.closed)
      return;
    this.buffer.push(value);
    if (this.buffer.length > this.bufferLimit) {
      const drop = this.buffer.length - this.bufferLimit;
      this.buffer.splice(0, drop);
      this.base += drop;
      for (const cursor of this.cursors) {
        if (cursor.position < this.base)
          cursor.position = this.base;
      }
    }
    const lastPos = this.base + this.buffer.length - 1;
    for (const cursor of this.cursors) {
      if (cursor.waiter && cursor.position <= lastPos) {
        const idx = cursor.position - this.base;
        const item = this.buffer[idx];
        cursor.position += 1;
        const w = cursor.waiter;
        cursor.waiter = null;
        w.resolve({ value: item, done: false });
      }
    }
    this.trim();
  }
  /**
   * Close the queue. New readers see immediate end-of-stream. Existing
   * readers can still drain values that were published before close;
   * once their cursor reaches the end of the buffer they see end-of-stream.
   */
  close() {
    if (this.closed)
      return;
    this.closed = true;
    for (const cursor of this.cursors) {
      if (cursor.waiter && cursor.position - this.base >= this.buffer.length) {
        const w = cursor.waiter;
        cursor.waiter = null;
        w.resolve({ value: void 0, done: true });
      }
    }
  }
  /** Create a new independent reader. */
  reader() {
    const cursor = {
      position: this.base + this.buffer.length,
      waiter: null,
      detached: this.closed
    };
    if (!this.closed)
      this.cursors.add(cursor);
    const queue = this;
    const detach = () => {
      if (!cursor.detached) {
        cursor.detached = true;
        queue.cursors.delete(cursor);
        queue.trim();
      }
    };
    const iter = {
      [Symbol.asyncIterator]() {
        return this;
      },
      next() {
        if (cursor.detached) {
          return Promise.resolve({ value: void 0, done: true });
        }
        const idx = cursor.position - queue.base;
        if (idx >= 0 && idx < queue.buffer.length) {
          const item = queue.buffer[idx];
          cursor.position += 1;
          queue.trim();
          return Promise.resolve({ value: item, done: false });
        }
        if (queue.closed) {
          return Promise.resolve({ value: void 0, done: true });
        }
        return new Promise((resolve) => {
          cursor.waiter = { resolve };
        });
      },
      return() {
        detach();
        return Promise.resolve({ value: void 0, done: true });
      }
    };
    return iter;
  }
  [Symbol.asyncIterator]() {
    return this.reader();
  }
  /** Drop buffer entries that every cursor has already consumed. */
  trim() {
    if (this.cursors.size === 0) {
      const dropped = this.buffer.length;
      if (dropped > 0) {
        this.buffer = [];
        this.base += dropped;
      }
      return;
    }
    let minPos = Infinity;
    for (const cursor of this.cursors) {
      if (cursor.position < minPos)
        minPos = cursor.position;
    }
    const drop = minPos - this.base;
    if (drop > 0) {
      this.buffer.splice(0, drop);
      this.base += drop;
    }
  }
};

// node_modules/@microsoft/agent-host-protocol/dist/client/error.js
var AhpClientError = class extends Error {
  constructor(message, options) {
    super(message, options);
    this.name = "AhpClientError";
  }
};
var RpcError = class extends AhpClientError {
  /** JSON-RPC numeric error code. See `JsonRpcErrorCodes` and `AhpErrorCodes`. */
  code;
  /** Optional structured payload included in the response. */
  data;
  constructor(code, message, data) {
    super(`RPC error ${code}: ${message}`);
    this.name = "RpcError";
    this.code = code;
    this.data = data;
  }
};
var RpcTimeoutError = class extends AhpClientError {
  /** The JSON-RPC method name that timed out. */
  method;
  /** The configured timeout in milliseconds that was exceeded. */
  timeoutMs;
  constructor(method, timeoutMs) {
    super(`Request "${method}" timed out after ${timeoutMs}ms`);
    this.name = "RpcTimeoutError";
    this.method = method;
    this.timeoutMs = timeoutMs;
  }
};
var TransportError = class extends AhpClientError {
  /** What kind of transport failure this represents. */
  kind;
  constructor(kind, message, options) {
    super(message, options);
    this.name = "TransportError";
    this.kind = kind;
  }
};
var ClientClosedError = class extends AhpClientError {
  constructor(message = "client shut down") {
    super(message);
    this.name = "ClientClosedError";
  }
};

// node_modules/@microsoft/agent-host-protocol/dist/client/transport.js
function encodeMessage(message) {
  return JSON.stringify(message);
}
function decodeMessage(text) {
  try {
    return JSON.parse(text);
  } catch (cause) {
    throw new TransportError("protocol", `invalid JSON: ${cause.message}`, { cause });
  }
}

// node_modules/@microsoft/agent-host-protocol/dist/client/client.js
var DEFAULT_REQUEST_TIMEOUT_MS = 3e4;
var DEFAULT_SUBSCRIPTION_BUFFER = 4096;
function noop() {
}
var Subscription = class {
  /** Channel URI this subscription is bound to. */
  uri;
  /** @internal */
  inner;
  /** @internal */
  constructor(uri, inner) {
    this.uri = uri;
    this.inner = inner;
  }
  next() {
    return this.inner.next();
  }
  return() {
    return this.inner.return ? this.inner.return() : Promise.resolve({ value: void 0, done: true });
  }
  [Symbol.asyncIterator]() {
    return this;
  }
  /** Terminate this consumer's iterator. Does not unsubscribe server-side. */
  async close() {
    await this.return();
  }
};
function createResourceRequestHandler(handlers) {
  return (async (method, params) => {
    const handler = handlers[method];
    if (!handler) {
      throw new RpcError(JsonRpcErrorCodes.MethodNotFound, `no handler for server method "${method}"`);
    }
    return handler(params);
  });
}
var AhpClient = class {
  transport;
  requestTimeoutMs;
  subscriptionBuffer;
  pending = /* @__PURE__ */ new Map();
  subscriptions = /* @__PURE__ */ new Map();
  allEvents = new AsyncBroadcastQueue();
  stateQueue = new AsyncBroadcastQueue();
  nextRequestId = 1;
  nextClientSeq = 1;
  state = { status: "idle" };
  receiveLoop = null;
  serverRequestHandler = null;
  constructor(transport, config2 = {}) {
    this.transport = transport;
    const timeout = config2.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS;
    this.requestTimeoutMs = timeout > 0 ? timeout : 0;
    const buffer = config2.subscriptionBuffer ?? DEFAULT_SUBSCRIPTION_BUFFER;
    this.subscriptionBuffer = buffer >= 1 ? Math.floor(buffer) : 1;
  }
  /** Current connection state. */
  get connectionState() {
    return this.state;
  }
  /** AsyncIterable stream of connection-state transitions. */
  stateChanges() {
    return this.stateQueue.reader();
  }
  /**
   * Top-level fan-in stream of every inbound event from this client.
   *
   * Each call returns a fresh independent iterator. Events are also
   * delivered to the matching per-URI {@link Subscription}.
   */
  events() {
    return this.allEvents.reader();
  }
  /**
   * Install a handler for server-initiated requests
   * ({@link ServerCommandMap}). If no handler is installed, the client
   * responds with a JSON-RPC `MethodNotFound` error so the server does
   * not leak pending requests.
   */
  setServerRequestHandler(handler) {
    this.serverRequestHandler = handler;
  }
  /**
   * Install typed per-method handlers for inbound server-initiated resource
   * requests ({@link ServerCommandMap}). Sugar over
   * {@link AhpClient.setServerRequestHandler} +
   * {@link createResourceRequestHandler}: a method left undefined is reported
   * to the peer as JSON-RPC `MethodNotFound`. Pass `null` to clear the
   * installed handler.
   */
  setResourceRequestHandlers(handlers) {
    this.setServerRequestHandler(handlers ? createResourceRequestHandler(handlers) : null);
  }
  /**
   * Start the inbound receive loop. Idempotent — calling more than once
   * is a no-op.
   */
  connect() {
    if (this.receiveLoop)
      return;
    this.setState({ status: "connected" });
    this.receiveLoop = this.driveTransport();
  }
  /**
   * Gracefully shut down the client. Closes the transport, rejects every
   * pending request with {@link ClientClosedError}, and terminates all
   * subscription and event streams.
   */
  async shutdown() {
    if (this.state.status === "closing" || this.state.status === "closed")
      return;
    this.setState({ status: "closing" });
    this.tearDown({ type: "shutdown" });
    try {
      await this.transport.close();
    } catch {
    }
    if (this.receiveLoop) {
      try {
        await this.receiveLoop;
      } catch {
      }
    }
  }
  // ─── Typed protocol helpers ────────────────────────────────────────────────
  /**
   * Send the `initialize` handshake. MUST be the first request after
   * {@link AhpClient.connect}.
   */
  async initialize(args) {
    const params = {
      channel: "ahp-root://",
      clientId: args.clientId,
      protocolVersions: [...args.protocolVersions],
      ...args.initialSubscriptions && args.initialSubscriptions.length > 0 ? { initialSubscriptions: [...args.initialSubscriptions] } : {},
      ...args.locale !== void 0 ? { locale: args.locale } : {}
    };
    return this.request("initialize", params);
  }
  /** Re-establish a dropped connection. */
  async reconnect(args) {
    const params = {
      channel: "ahp-root://",
      clientId: args.clientId,
      lastSeenServerSeq: args.lastSeenServerSeq,
      subscriptions: [...args.subscriptions]
    };
    return this.request("reconnect", params);
  }
  /**
   * Subscribe to a URI and obtain a {@link Subscription} that streams
   * subsequent events. The returned subscription is registered locally
   * before the `subscribe` request is sent, so no events delivered during
   * the round-trip are missed.
   */
  async subscribe(uri, options = {}) {
    const subscription = this.attachSubscription(uri);
    try {
      const params = {
        channel: uri,
        ...options.delivery ? { delivery: options.delivery } : {},
        ...options.view ? { view: options.view } : {}
      };
      const result = await this.request("subscribe", params);
      return { result, subscription };
    } catch (err) {
      await subscription.close();
      throw err;
    }
  }
  /**
   * Attach a new local {@link Subscription} without sending a `subscribe`
   * request — use this when the URI was included in `initialSubscriptions`
   * during {@link AhpClient.initialize}, or to add an additional consumer
   * for a URI that is already subscribed.
   *
   * Throws {@link ClientClosedError} after the client has been shut down.
   */
  attachSubscription(uri) {
    this.assertOpen();
    let queue = this.subscriptions.get(uri);
    if (!queue) {
      queue = new AsyncBroadcastQueue(this.subscriptionBuffer);
      this.subscriptions.set(uri, queue);
    }
    return new Subscription(uri, queue.reader());
  }
  /**
   * Send an `unsubscribe` notification and drop the local fan-out for
   * this URI. Any active {@link Subscription} iterators terminate.
   *
   * No-op after the client has been shut down.
   */
  async unsubscribe(uri) {
    if (this.isClosed())
      return;
    const queue = this.subscriptions.get(uri);
    if (queue) {
      this.subscriptions.delete(uri);
      queue.close();
    }
    const params = { channel: uri };
    this.notify("unsubscribe", params);
    return Promise.resolve();
  }
  /**
   * Fire a write-ahead `dispatchAction` notification.
   *
   * If `clientSeq` is omitted, the client uses its internal monotonic
   * counter. If supplied, the counter advances to `max(current,
   * clientSeq + 1)` so subsequent auto-assigned sequences remain
   * monotonic.
   *
   * Throws {@link ClientClosedError} after the client has been shut down.
   */
  dispatch(channel, action, clientSeq) {
    this.assertOpen();
    const seq = clientSeq ?? this.nextClientSeq;
    if (clientSeq !== void 0) {
      if (seq + 1 > this.nextClientSeq)
        this.nextClientSeq = seq + 1;
    } else {
      this.nextClientSeq = seq + 1;
    }
    const params = { channel, clientSeq: seq, action };
    this.notify("dispatchAction", params);
    return { clientSeq: seq };
  }
  /**
   * Protocol-level liveness ping. Useful in browsers, which cannot send
   * WebSocket ping frames directly.
   *
   * `ping` is a connection-level command; its channel is always
   * `ahp-root://`.
   */
  async ping() {
    const params = { channel: "ahp-root://" };
    await this.request("ping", params);
  }
  // ─── Resource commands ─────────────────────────────────────────────────────
  //
  // Typed convenience wrappers over the symmetrical `resource*` family. Each
  // targets the root channel (`ahp-root://`), so callers omit `channel`. The
  // reverse direction — a server calling these on the client — is handled via
  // {@link AhpClient.setResourceRequestHandlers}.
  /** Read the content of a resource by URI (`resourceRead`). */
  async resourceRead(params) {
    return this.request("resourceRead", { ...params, channel: "ahp-root://" });
  }
  /** Write content to a file on the receiver's filesystem (`resourceWrite`). */
  async resourceWrite(params) {
    return this.request("resourceWrite", { ...params, channel: "ahp-root://" });
  }
  /** List directory entries at a file URI (`resourceList`). */
  async resourceList(params) {
    return this.request("resourceList", { ...params, channel: "ahp-root://" });
  }
  /** Copy a resource from one URI to another (`resourceCopy`). */
  async resourceCopy(params) {
    return this.request("resourceCopy", { ...params, channel: "ahp-root://" });
  }
  /** Delete a resource at a URI (`resourceDelete`). */
  async resourceDelete(params) {
    return this.request("resourceDelete", { ...params, channel: "ahp-root://" });
  }
  /** Move (rename) a resource from one URI to another (`resourceMove`). */
  async resourceMove(params) {
    return this.request("resourceMove", { ...params, channel: "ahp-root://" });
  }
  /** Resolve a resource — `stat` + `realpath` (`resourceResolve`). */
  async resourceResolve(params) {
    return this.request("resourceResolve", { ...params, channel: "ahp-root://" });
  }
  /** Create a directory with `mkdir -p` semantics (`resourceMkdir`). */
  async resourceMkdir(params) {
    return this.request("resourceMkdir", { ...params, channel: "ahp-root://" });
  }
  /** Request permission to access a resource (`resourceRequest`). */
  async resourceRequest(params) {
    return this.request("resourceRequest", { ...params, channel: "ahp-root://" });
  }
  /**
   * Create a resource watcher (`createResourceWatch`). Returns the
   * `ahp-resource-watch:/<id>` channel URI; {@link AhpClient.subscribe} to it
   * to receive change events, and {@link AhpClient.unsubscribe} to release the
   * watcher.
   */
  async createResourceWatch(params) {
    return this.request("createResourceWatch", {
      ...params,
      channel: "ahp-root://"
    });
  }
  // ─── Completions commands ──────────────────────────────────────────────────
  /**
   * Request inline completion items for a partially-typed input
   * (`completions`), e.g. to power `@`-mention pickers. Unlike the `resource*`
   * wrappers, the caller-supplied `channel` (the chat URI the completion is
   * scoped to) is preserved. Debounce calls to avoid flooding the server on
   * every keystroke.
   */
  async completions(params) {
    return this.request("completions", params);
  }
  /**
   * Query the server for allowed values of a dynamic session config property
   * (`sessionConfigCompletions`). Targets the root channel, so callers omit
   * `channel`.
   */
  async sessionConfigCompletions(params) {
    return this.request("sessionConfigCompletions", {
      ...params,
      channel: "ahp-root://"
    });
  }
  // ─── Lower-level JSON-RPC ──────────────────────────────────────────────────
  /** Send a JSON-RPC request and await its result. */
  async request(method, params) {
    this.assertOpen();
    const id = this.nextRequestId++;
    const msg = {
      jsonrpc: "2.0",
      id,
      method,
      params
    };
    return new Promise((resolve, reject) => {
      const pending = {
        resolve: (value) => resolve(value),
        reject,
        method,
        timer: null
      };
      this.pending.set(id, pending);
      if (this.requestTimeoutMs > 0) {
        pending.timer = setTimeout(() => {
          if (this.pending.delete(id)) {
            reject(new RpcTimeoutError(method, this.requestTimeoutMs));
          }
        }, this.requestTimeoutMs);
      }
      this.sendMessage(msg).catch((err) => {
        if (this.pending.delete(id)) {
          if (pending.timer)
            clearTimeout(pending.timer);
          reject(err);
        }
      });
    });
  }
  /**
   * Send a JSON-RPC notification (fire-and-forget).
   *
   * Throws {@link ClientClosedError} after the client has been shut down.
   * Transport-level send failures surface synchronously via
   * {@link AhpClient.connectionState} (the receive loop also tears down
   * on the next inbound failure).
   */
  notify(method, params) {
    this.assertOpen();
    const msg = {
      jsonrpc: "2.0",
      method,
      params
    };
    this.sendMessage(msg).catch(noop);
  }
  // ─── Internals ─────────────────────────────────────────────────────────────
  isClosed() {
    return this.state.status === "closing" || this.state.status === "closed";
  }
  assertOpen() {
    if (this.isClosed())
      throw new ClientClosedError();
  }
  async sendMessage(msg) {
    try {
      await this.transport.send(msg);
    } catch (err) {
      const te = err instanceof TransportError ? err : new TransportError("io", `transport send failed: ${err.message}`, { cause: err });
      this.tearDown({ type: "transport", error: te });
      throw te;
    }
  }
  setState(next) {
    this.state = next;
    this.stateQueue.publish(next);
  }
  tearDown(reason) {
    if (this.state.status === "closed")
      return;
    this.setState({ status: "closed", reason });
    const failure = reason.type === "shutdown" ? new ClientClosedError() : reason.error;
    for (const [id, pending] of this.pending) {
      if (pending.timer)
        clearTimeout(pending.timer);
      try {
        pending.reject(failure);
      } catch {
      }
      this.pending.delete(id);
    }
    for (const queue of this.subscriptions.values())
      queue.close();
    this.subscriptions.clear();
    this.allEvents.close();
    this.stateQueue.close();
  }
  async driveTransport() {
    try {
      while (this.state.status === "connected") {
        const frame = await this.transport.recv();
        if (frame === null) {
          this.tearDown({ type: "transport", error: new TransportError("closed", "transport closed") });
          return;
        }
        this.handleFrame(frame);
      }
    } catch (err) {
      const te = err instanceof TransportError ? err : new TransportError("io", `transport recv failed: ${err.message}`, { cause: err });
      this.tearDown({ type: "transport", error: te });
    }
  }
  handleFrame(frame) {
    let message;
    try {
      switch (frame.kind) {
        case "parsed":
          message = frame.message;
          break;
        case "text":
          message = decodeMessage(frame.text);
          break;
        case "binary": {
          const text = new TextDecoder("utf-8").decode(frame.data);
          message = decodeMessage(text);
          break;
        }
      }
    } catch (err) {
      console.warn(`AhpClient: malformed inbound frame: ${err.message}`);
      return;
    }
    this.dispatchInbound(message);
  }
  dispatchInbound(message) {
    if ("id" in message && "result" in message) {
      const success = message;
      const pending = this.pending.get(success.id);
      if (pending) {
        this.pending.delete(success.id);
        if (pending.timer)
          clearTimeout(pending.timer);
        pending.resolve(success.result);
      }
      return;
    }
    if ("id" in message && "error" in message) {
      const failure = message;
      const pending = this.pending.get(failure.id);
      if (pending) {
        this.pending.delete(failure.id);
        if (pending.timer)
          clearTimeout(pending.timer);
        pending.reject(new RpcError(failure.error.code, failure.error.message, failure.error.data));
      }
      return;
    }
    if ("id" in message && "method" in message) {
      void this.handleServerRequest(message);
      return;
    }
    if ("method" in message) {
      this.handleNotification(message);
      return;
    }
  }
  async handleServerRequest(req) {
    if (this.serverRequestHandler) {
      try {
        const handler = this.serverRequestHandler;
        const result = await handler(req.method, req.params);
        const response2 = {
          jsonrpc: "2.0",
          id: req.id,
          result
        };
        this.sendMessage(response2).catch(noop);
      } catch (err) {
        const code = err instanceof RpcError ? err.code : JsonRpcErrorCodes.InternalError;
        const message = err instanceof Error ? err.message : String(err);
        const data = err instanceof RpcError ? err.data : void 0;
        const response2 = {
          jsonrpc: "2.0",
          id: req.id,
          error: data !== void 0 ? { code, message, data } : { code, message }
        };
        this.sendMessage(response2).catch(noop);
      }
      return;
    }
    const response = {
      jsonrpc: "2.0",
      id: req.id,
      error: {
        code: JsonRpcErrorCodes.MethodNotFound,
        message: `no handler for server method "${req.method}"`
      }
    };
    this.sendMessage(response).catch(noop);
  }
  handleNotification(n) {
    const params = n.params ?? {};
    const channel = params.channel;
    switch (n.method) {
      case "action": {
        const env = n.params;
        this.fanOut(env.channel, { type: "action", params: env });
        break;
      }
      case "root/sessionAdded": {
        const p = n.params;
        this.fanOut(p.channel, { type: "sessionAdded", params: p });
        break;
      }
      case "root/sessionRemoved": {
        const p = n.params;
        this.fanOut(p.channel, { type: "sessionRemoved", params: p });
        break;
      }
      case "root/sessionSummaryChanged": {
        const p = n.params;
        this.fanOut(p.channel, { type: "sessionSummaryChanged", params: p });
        break;
      }
      case "auth/required": {
        const p = n.params;
        this.fanOut(p.channel, { type: "authRequired", params: p });
        break;
      }
      default:
        void channel;
        break;
    }
  }
  fanOut(channel, event) {
    const queue = this.subscriptions.get(channel);
    if (queue)
      queue.publish(event);
    this.allEvents.publish({ channel, event });
  }
};

// node_modules/@microsoft/agent-host-protocol/dist/types/common/actions.js
var ActionType;
(function(ActionType2) {
  ActionType2["RootAgentsChanged"] = "root/agentsChanged";
  ActionType2["RootActiveSessionsChanged"] = "root/activeSessionsChanged";
  ActionType2["SessionReady"] = "session/ready";
  ActionType2["SessionCreationFailed"] = "session/creationFailed";
  ActionType2["SessionChatAdded"] = "session/chatAdded";
  ActionType2["SessionChatRemoved"] = "session/chatRemoved";
  ActionType2["SessionChatUpdated"] = "session/chatUpdated";
  ActionType2["SessionDefaultChatChanged"] = "session/defaultChatChanged";
  ActionType2["ChatTurnStarted"] = "chat/turnStarted";
  ActionType2["ChatDelta"] = "chat/delta";
  ActionType2["ChatResponsePart"] = "chat/responsePart";
  ActionType2["ChatToolCallStart"] = "chat/toolCallStart";
  ActionType2["ChatToolCallDelta"] = "chat/toolCallDelta";
  ActionType2["ChatToolCallReady"] = "chat/toolCallReady";
  ActionType2["ChatToolCallConfirmed"] = "chat/toolCallConfirmed";
  ActionType2["ChatToolCallComplete"] = "chat/toolCallComplete";
  ActionType2["ChatToolCallResultConfirmed"] = "chat/toolCallResultConfirmed";
  ActionType2["ChatToolCallContentChanged"] = "chat/toolCallContentChanged";
  ActionType2["ChatToolCallAuthRequired"] = "chat/toolCallAuthRequired";
  ActionType2["ChatToolCallAuthResolved"] = "chat/toolCallAuthResolved";
  ActionType2["ChatTurnComplete"] = "chat/turnComplete";
  ActionType2["ChatTurnCancelled"] = "chat/turnCancelled";
  ActionType2["ChatError"] = "chat/error";
  ActionType2["ChatTurnResume"] = "chat/turnResume";
  ActionType2["ChatActivityChanged"] = "chat/activityChanged";
  ActionType2["ChatWorkingDirectorySet"] = "chat/workingDirectorySet";
  ActionType2["ChatWorkingDirectoryRemoved"] = "chat/workingDirectoryRemoved";
  ActionType2["SessionTitleChanged"] = "session/titleChanged";
  ActionType2["ChatUsage"] = "chat/usage";
  ActionType2["ChatReasoning"] = "chat/reasoning";
  ActionType2["SessionServerToolsChanged"] = "session/serverToolsChanged";
  ActionType2["SessionActiveClientSet"] = "session/activeClientSet";
  ActionType2["SessionActiveClientRemoved"] = "session/activeClientRemoved";
  ActionType2["SessionWorkingDirectorySet"] = "session/workingDirectorySet";
  ActionType2["SessionWorkingDirectoryRemoved"] = "session/workingDirectoryRemoved";
  ActionType2["SessionWorkingDirectoryReplaced"] = "session/workingDirectoryReplaced";
  ActionType2["SessionInputNeededSet"] = "session/inputNeededSet";
  ActionType2["SessionInputNeededRemoved"] = "session/inputNeededRemoved";
  ActionType2["ChatPendingMessageSet"] = "chat/pendingMessageSet";
  ActionType2["ChatPendingMessageRemoved"] = "chat/pendingMessageRemoved";
  ActionType2["ChatQueuedMessagesReordered"] = "chat/queuedMessagesReordered";
  ActionType2["ChatDraftChanged"] = "chat/draftChanged";
  ActionType2["ChatInputRequested"] = "chat/inputRequested";
  ActionType2["ChatInputAnswerChanged"] = "chat/inputAnswerChanged";
  ActionType2["ChatInputCompleted"] = "chat/inputCompleted";
  ActionType2["SessionCustomizationsChanged"] = "session/customizationsChanged";
  ActionType2["SessionCustomizationToggled"] = "session/customizationToggled";
  ActionType2["SessionCustomizationUpdated"] = "session/customizationUpdated";
  ActionType2["SessionCustomizationRemoved"] = "session/customizationRemoved";
  ActionType2["SessionMcpServerStateChanged"] = "session/mcpServerStateChanged";
  ActionType2["SessionMcpServerStartRequested"] = "session/mcpServerStartRequested";
  ActionType2["SessionMcpServerStopRequested"] = "session/mcpServerStopRequested";
  ActionType2["ChatTruncated"] = "chat/truncated";
  ActionType2["ChatTurnsLoaded"] = "chat/turnsLoaded";
  ActionType2["SessionIsReadChanged"] = "session/isReadChanged";
  ActionType2["SessionIsArchivedChanged"] = "session/isArchivedChanged";
  ActionType2["SessionActivityChanged"] = "session/activityChanged";
  ActionType2["SessionChangesetsChanged"] = "session/changesetsChanged";
  ActionType2["SessionConfigChanged"] = "session/configChanged";
  ActionType2["SessionMetaChanged"] = "session/metaChanged";
  ActionType2["ChangesetStatusChanged"] = "changeset/statusChanged";
  ActionType2["ChangesetFileSet"] = "changeset/fileSet";
  ActionType2["ChangesetFileRemoved"] = "changeset/fileRemoved";
  ActionType2["ChangesetFilesReviewChanged"] = "changeset/filesReviewChanged";
  ActionType2["ChangesetContentChanged"] = "changeset/contentChanged";
  ActionType2["ChangesetOperationsChanged"] = "changeset/operationsChanged";
  ActionType2["ChangesetOperationStatusChanged"] = "changeset/operationStatusChanged";
  ActionType2["ChangesetCleared"] = "changeset/cleared";
  ActionType2["AnnotationsSet"] = "annotations/set";
  ActionType2["AnnotationsUpdated"] = "annotations/updated";
  ActionType2["AnnotationsRemoved"] = "annotations/removed";
  ActionType2["AnnotationsEntrySet"] = "annotations/entrySet";
  ActionType2["AnnotationsEntryRemoved"] = "annotations/entryRemoved";
  ActionType2["RootTerminalsChanged"] = "root/terminalsChanged";
  ActionType2["RootConfigChanged"] = "root/configChanged";
  ActionType2["TerminalData"] = "terminal/data";
  ActionType2["TerminalInput"] = "terminal/input";
  ActionType2["TerminalResized"] = "terminal/resized";
  ActionType2["TerminalClaimed"] = "terminal/claimed";
  ActionType2["TerminalTitleChanged"] = "terminal/titleChanged";
  ActionType2["TerminalCwdChanged"] = "terminal/cwdChanged";
  ActionType2["TerminalExited"] = "terminal/exited";
  ActionType2["TerminalCleared"] = "terminal/cleared";
  ActionType2["TerminalCommandDetectionAvailable"] = "terminal/commandDetectionAvailable";
  ActionType2["TerminalCommandExecuted"] = "terminal/commandExecuted";
  ActionType2["TerminalCommandFinished"] = "terminal/commandFinished";
  ActionType2["ResourceWatchChanged"] = "resourceWatch/changed";
  ActionType2["AutomationCreateRequested"] = "automation/createRequested";
  ActionType2["AutomationUpdateRequested"] = "automation/updateRequested";
  ActionType2["AutomationSet"] = "automation/set";
  ActionType2["AutomationRemoved"] = "automation/removed";
  ActionType2["AutomationRunLifecycleChanged"] = "automationRun/lifecycleChanged";
  ActionType2["AutomationRunSessionSet"] = "automationRun/sessionSet";
  ActionType2["AutomationRunSessionRemoved"] = "automationRun/sessionRemoved";
  ActionType2["AutomationRunPrimarySessionChanged"] = "automationRun/primarySessionChanged";
  ActionType2["AutomationRunCancelRequested"] = "automationRun/cancelRequested";
})(ActionType || (ActionType = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-changeset/state.js
var ChangesetStatus;
(function(ChangesetStatus2) {
  ChangesetStatus2["Computing"] = "computing";
  ChangesetStatus2["Ready"] = "ready";
  ChangesetStatus2["Error"] = "error";
})(ChangesetStatus || (ChangesetStatus = {}));
var ChangesetOperationStatus;
(function(ChangesetOperationStatus2) {
  ChangesetOperationStatus2["Idle"] = "idle";
  ChangesetOperationStatus2["Running"] = "running";
  ChangesetOperationStatus2["Error"] = "error";
  ChangesetOperationStatus2["Disabled"] = "disabled";
})(ChangesetOperationStatus || (ChangesetOperationStatus = {}));
var ChangesetOperationScope;
(function(ChangesetOperationScope2) {
  ChangesetOperationScope2["Changeset"] = "changeset";
  ChangesetOperationScope2["Resource"] = "resource";
  ChangesetOperationScope2["Range"] = "range";
})(ChangesetOperationScope || (ChangesetOperationScope = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/action-origin.generated.js
var IS_CLIENT_DISPATCHABLE = {
  [ActionType.RootAgentsChanged]: false,
  [ActionType.RootActiveSessionsChanged]: false,
  [ActionType.RootTerminalsChanged]: false,
  [ActionType.RootConfigChanged]: true,
  [ActionType.SessionReady]: false,
  [ActionType.SessionCreationFailed]: false,
  [ActionType.SessionChatAdded]: false,
  [ActionType.SessionChatRemoved]: false,
  [ActionType.SessionChatUpdated]: false,
  [ActionType.SessionDefaultChatChanged]: false,
  [ActionType.SessionTitleChanged]: true,
  [ActionType.SessionServerToolsChanged]: false,
  [ActionType.SessionActiveClientSet]: true,
  [ActionType.SessionActiveClientRemoved]: true,
  [ActionType.SessionWorkingDirectorySet]: true,
  [ActionType.SessionWorkingDirectoryRemoved]: true,
  [ActionType.SessionWorkingDirectoryReplaced]: true,
  [ActionType.SessionInputNeededSet]: false,
  [ActionType.SessionInputNeededRemoved]: false,
  [ActionType.SessionCustomizationsChanged]: false,
  [ActionType.SessionCustomizationToggled]: true,
  [ActionType.SessionCustomizationUpdated]: false,
  [ActionType.SessionCustomizationRemoved]: false,
  [ActionType.SessionMcpServerStateChanged]: false,
  [ActionType.SessionMcpServerStartRequested]: true,
  [ActionType.SessionMcpServerStopRequested]: true,
  [ActionType.SessionIsReadChanged]: true,
  [ActionType.SessionIsArchivedChanged]: true,
  [ActionType.SessionActivityChanged]: false,
  [ActionType.SessionChangesetsChanged]: false,
  [ActionType.SessionConfigChanged]: true,
  [ActionType.SessionMetaChanged]: false,
  [ActionType.ChatTurnStarted]: true,
  [ActionType.ChatDelta]: false,
  [ActionType.ChatResponsePart]: false,
  [ActionType.ChatToolCallStart]: false,
  [ActionType.ChatToolCallDelta]: false,
  [ActionType.ChatToolCallReady]: false,
  [ActionType.ChatToolCallConfirmed]: true,
  [ActionType.ChatToolCallComplete]: true,
  [ActionType.ChatToolCallResultConfirmed]: true,
  [ActionType.ChatToolCallContentChanged]: true,
  [ActionType.ChatToolCallAuthRequired]: false,
  [ActionType.ChatToolCallAuthResolved]: false,
  [ActionType.ChatTurnComplete]: false,
  [ActionType.ChatTurnCancelled]: true,
  [ActionType.ChatError]: false,
  [ActionType.ChatTurnResume]: true,
  [ActionType.ChatActivityChanged]: false,
  [ActionType.ChatWorkingDirectorySet]: true,
  [ActionType.ChatWorkingDirectoryRemoved]: true,
  [ActionType.ChatUsage]: false,
  [ActionType.ChatReasoning]: false,
  [ActionType.ChatPendingMessageSet]: true,
  [ActionType.ChatPendingMessageRemoved]: true,
  [ActionType.ChatQueuedMessagesReordered]: true,
  [ActionType.ChatDraftChanged]: true,
  [ActionType.ChatInputRequested]: false,
  [ActionType.ChatInputAnswerChanged]: true,
  [ActionType.ChatInputCompleted]: true,
  [ActionType.ChatTruncated]: true,
  [ActionType.ChatTurnsLoaded]: false,
  [ActionType.ChangesetStatusChanged]: false,
  [ActionType.ChangesetFileSet]: false,
  [ActionType.ChangesetFileRemoved]: false,
  [ActionType.ChangesetFilesReviewChanged]: true,
  [ActionType.ChangesetContentChanged]: false,
  [ActionType.ChangesetOperationsChanged]: false,
  [ActionType.ChangesetOperationStatusChanged]: false,
  [ActionType.ChangesetCleared]: false,
  [ActionType.AnnotationsSet]: true,
  [ActionType.AnnotationsUpdated]: true,
  [ActionType.AnnotationsRemoved]: true,
  [ActionType.AnnotationsEntrySet]: true,
  [ActionType.AnnotationsEntryRemoved]: true,
  [ActionType.TerminalData]: false,
  [ActionType.TerminalInput]: true,
  [ActionType.TerminalResized]: true,
  [ActionType.TerminalClaimed]: true,
  [ActionType.TerminalTitleChanged]: true,
  [ActionType.TerminalCwdChanged]: false,
  [ActionType.TerminalExited]: false,
  [ActionType.TerminalCleared]: true,
  [ActionType.TerminalCommandDetectionAvailable]: false,
  [ActionType.TerminalCommandExecuted]: false,
  [ActionType.TerminalCommandFinished]: false,
  [ActionType.ResourceWatchChanged]: false,
  [ActionType.AutomationCreateRequested]: true,
  [ActionType.AutomationUpdateRequested]: true,
  [ActionType.AutomationSet]: false,
  [ActionType.AutomationRemoved]: true,
  [ActionType.AutomationRunLifecycleChanged]: false,
  [ActionType.AutomationRunSessionSet]: false,
  [ActionType.AutomationRunSessionRemoved]: false,
  [ActionType.AutomationRunPrimarySessionChanged]: false,
  [ActionType.AutomationRunCancelRequested]: true
};

// node_modules/@microsoft/agent-host-protocol/dist/types/common/reducer-helpers.js
function softAssertNever(value, log) {
  const msg = `Unhandled action type: ${JSON.stringify(value)}`;
  (log ?? console.warn)(msg);
}

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-root/reducer.js
function rootReducer(state, action, log) {
  switch (action.type) {
    case ActionType.RootAgentsChanged:
      return { ...state, agents: action.agents };
    case ActionType.RootActiveSessionsChanged:
      return { ...state, activeSessions: action.activeSessions };
    case ActionType.RootTerminalsChanged:
      return { ...state, terminals: action.terminals };
    case ActionType.RootConfigChanged:
      if (!state.config) {
        return state;
      }
      return {
        ...state,
        config: {
          ...state.config,
          values: action.replace ? { ...action.config } : { ...state.config.values, ...action.config }
        }
      };
    default:
      softAssertNever(action, log);
      return state;
  }
}

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-session/state.js
var SessionLifecycle;
(function(SessionLifecycle2) {
  SessionLifecycle2["Creating"] = "creating";
  SessionLifecycle2["Ready"] = "ready";
  SessionLifecycle2["Failed"] = "failed";
})(SessionLifecycle || (SessionLifecycle = {}));
var SessionStatus;
(function(SessionStatus2) {
  SessionStatus2[SessionStatus2["Idle"] = 1] = "Idle";
  SessionStatus2[SessionStatus2["Error"] = 2] = "Error";
  SessionStatus2[SessionStatus2["InProgress"] = 8] = "InProgress";
  SessionStatus2[SessionStatus2["InputNeeded"] = 24] = "InputNeeded";
  SessionStatus2[SessionStatus2["IsRead"] = 32] = "IsRead";
  SessionStatus2[SessionStatus2["IsArchived"] = 64] = "IsArchived";
})(SessionStatus || (SessionStatus = {}));
var SessionOriginKind;
(function(SessionOriginKind2) {
  SessionOriginKind2["Automation"] = "automation";
})(SessionOriginKind || (SessionOriginKind = {}));
var SessionInputRequestKind;
(function(SessionInputRequestKind2) {
  SessionInputRequestKind2["ChatInput"] = "chatInput";
  SessionInputRequestKind2["ToolConfirmation"] = "toolConfirmation";
  SessionInputRequestKind2["ToolClientExecution"] = "toolClientExecution";
  SessionInputRequestKind2["ToolAuthentication"] = "toolAuthentication";
})(SessionInputRequestKind || (SessionInputRequestKind = {}));
var CustomizationType;
(function(CustomizationType2) {
  CustomizationType2["Plugin"] = "plugin";
  CustomizationType2["Directory"] = "directory";
  CustomizationType2["Agent"] = "agent";
  CustomizationType2["Skill"] = "skill";
  CustomizationType2["Prompt"] = "prompt";
  CustomizationType2["Rule"] = "rule";
  CustomizationType2["Hook"] = "hook";
  CustomizationType2["McpServer"] = "mcpServer";
})(CustomizationType || (CustomizationType = {}));
var CustomizationEnablementKind;
(function(CustomizationEnablementKind2) {
  CustomizationEnablementKind2["Global"] = "global";
  CustomizationEnablementKind2["Workspace"] = "workspace";
  CustomizationEnablementKind2["Session"] = "session";
})(CustomizationEnablementKind || (CustomizationEnablementKind = {}));
var CustomizationLoadStatus;
(function(CustomizationLoadStatus2) {
  CustomizationLoadStatus2["Loading"] = "loading";
  CustomizationLoadStatus2["Loaded"] = "loaded";
  CustomizationLoadStatus2["Degraded"] = "degraded";
  CustomizationLoadStatus2["Error"] = "error";
})(CustomizationLoadStatus || (CustomizationLoadStatus = {}));
var McpServerStatus;
(function(McpServerStatus2) {
  McpServerStatus2["Starting"] = "starting";
  McpServerStatus2["Ready"] = "ready";
  McpServerStatus2["AuthRequired"] = "authRequired";
  McpServerStatus2["Error"] = "error";
  McpServerStatus2["Stopped"] = "stopped";
})(McpServerStatus || (McpServerStatus = {}));
var McpAuthRequiredReason;
(function(McpAuthRequiredReason2) {
  McpAuthRequiredReason2["Required"] = "required";
  McpAuthRequiredReason2["Expired"] = "expired";
  McpAuthRequiredReason2["InsufficientScope"] = "insufficientScope";
})(McpAuthRequiredReason || (McpAuthRequiredReason = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-session/reducer.js
var STATUS_ACTIVITY_MASK = (1 << 5) - 1;
function withStatusFlag(status, flag, set) {
  return set ? status | flag : status & ~flag;
}
function awaitsUser(request) {
  return request.kind !== SessionInputRequestKind.ToolClientExecution;
}
function withInputNeededStatus(status, inputNeeded) {
  if (inputNeeded.some(awaitsUser)) {
    return status & ~STATUS_ACTIVITY_MASK | SessionStatus.InputNeeded;
  }
  return status & ~(SessionStatus.InputNeeded & ~SessionStatus.InProgress);
}
function updateMcpServerCustomization(state, id, update) {
  const list = state.customizations;
  if (!list) {
    return state;
  }
  const topIdx = list.findIndex((c) => c.id === id);
  if (topIdx >= 0) {
    const entry = list[topIdx];
    if (entry.type !== CustomizationType.McpServer) {
      return state;
    }
    const updated2 = list.slice();
    updated2[topIdx] = update(entry);
    return { ...state, customizations: updated2 };
  }
  let changed = false;
  const updated = list.map((container) => {
    if (container.type === CustomizationType.McpServer) {
      return container;
    }
    const children = container.children;
    if (!children) {
      return container;
    }
    const childIdx = children.findIndex((c) => c.id === id);
    if (childIdx < 0) {
      return container;
    }
    const child = children[childIdx];
    if (child.type !== CustomizationType.McpServer) {
      return container;
    }
    changed = true;
    const newChildren = children.slice();
    newChildren[childIdx] = update(child);
    return { ...container, children: newChildren };
  });
  if (!changed) {
    return state;
  }
  return { ...state, customizations: updated };
}
function applyCustomizationEnablement(customization, enablement) {
  switch (customization.type) {
    case CustomizationType.Plugin:
    case CustomizationType.McpServer: {
      if (enablement.length > 0) {
        return { ...customization, enablement: [...enablement] };
      }
      const { enablement: _enablement, ...withoutEnablement } = customization;
      return withoutEnablement;
    }
    default:
      return { ...customization, enabled: enablement[0]?.enabled ?? true };
  }
}
function sessionReducer(state, action, log) {
  switch (action.type) {
    // ── Lifecycle ──────────────────────────────────────────────────────────
    case ActionType.SessionReady:
      return { ...state, lifecycle: SessionLifecycle.Ready };
    case ActionType.SessionCreationFailed:
      return {
        ...state,
        lifecycle: SessionLifecycle.Failed,
        creationError: action.error
      };
    case ActionType.SessionChatAdded: {
      const list = state.chats;
      const idx = list.findIndex((c) => c.resource === action.summary.resource);
      if (idx < 0) {
        return { ...state, chats: [...list, action.summary] };
      }
      const updated = list.slice();
      updated[idx] = action.summary;
      return { ...state, chats: updated };
    }
    case ActionType.SessionChatRemoved: {
      const list = state.chats;
      const idx = list.findIndex((c) => c.resource === action.chat);
      if (idx < 0) {
        return state;
      }
      const updated = list.slice();
      updated.splice(idx, 1);
      const next = { ...state, chats: updated };
      if (state.defaultChat === action.chat) {
        delete next.defaultChat;
      }
      return next;
    }
    case ActionType.SessionChatUpdated: {
      const list = state.chats;
      const idx = list.findIndex((c) => c.resource === action.chat);
      if (idx < 0) {
        return state;
      }
      const { resource: _ignored, ...changes } = action.changes;
      const updated = list.slice();
      updated[idx] = { ...list[idx], ...changes };
      return { ...state, chats: updated };
    }
    case ActionType.SessionDefaultChatChanged:
      return { ...state, defaultChat: action.defaultChat };
    // ── Metadata ──────────────────────────────────────────────────────────
    case ActionType.SessionTitleChanged:
      return { ...state, title: action.title };
    case ActionType.SessionIsReadChanged:
      return {
        ...state,
        status: withStatusFlag(state.status, SessionStatus.IsRead, action.isRead)
      };
    case ActionType.SessionIsArchivedChanged:
      return {
        ...state,
        status: withStatusFlag(state.status, SessionStatus.IsArchived, action.isArchived)
      };
    case ActionType.SessionActivityChanged:
      return { ...state, activity: action.activity };
    case ActionType.SessionChangesetsChanged: {
      const { changesets: _omit, ...stateWithoutChangesets } = state;
      return action.changesets ? { ...stateWithoutChangesets, changesets: action.changesets } : stateWithoutChangesets;
    }
    case ActionType.SessionConfigChanged:
      if (!state.config) {
        return state;
      }
      return {
        ...state,
        config: {
          ...state.config,
          values: action.replace ? { ...action.config } : { ...state.config.values, ...action.config }
        }
      };
    case ActionType.SessionMetaChanged:
      return { ...state, _meta: action._meta };
    case ActionType.SessionServerToolsChanged:
      return { ...state, serverTools: action.tools };
    case ActionType.SessionActiveClientSet: {
      const list = state.activeClients;
      const idx = list.findIndex((c) => c.clientId === action.activeClient.clientId);
      if (idx < 0) {
        return { ...state, activeClients: [...list, action.activeClient] };
      }
      const updated = list.slice();
      updated[idx] = action.activeClient;
      return { ...state, activeClients: updated };
    }
    case ActionType.SessionActiveClientRemoved: {
      const list = state.activeClients;
      const idx = list.findIndex((c) => c.clientId === action.clientId);
      if (idx < 0) {
        return state;
      }
      const updated = list.slice();
      updated.splice(idx, 1);
      return { ...state, activeClients: updated };
    }
    // ── Working Directories ─────────────────────────────────────────────
    case ActionType.SessionWorkingDirectorySet: {
      const list = state.workingDirectories ?? [];
      if (list.includes(action.directory)) {
        return state;
      }
      return { ...state, workingDirectories: [...list, action.directory] };
    }
    case ActionType.SessionWorkingDirectoryRemoved: {
      const list = state.workingDirectories;
      if (!list) {
        return state;
      }
      const idx = list.indexOf(action.directory);
      if (idx < 0) {
        return state;
      }
      const updated = list.slice();
      updated.splice(idx, 1);
      return { ...state, workingDirectories: updated };
    }
    case ActionType.SessionWorkingDirectoryReplaced: {
      const list = state.workingDirectories;
      if (!list) {
        return state;
      }
      const idx = list.indexOf(action.directory);
      if (idx < 0) {
        return state;
      }
      const replacementIdx = list.indexOf(action.replacement);
      if (replacementIdx >= 0 && replacementIdx < idx) {
        return {
          ...state,
          workingDirectories: list.filter((_, index) => index !== idx)
        };
      }
      return {
        ...state,
        workingDirectories: list.map((directory, index) => index === idx ? action.replacement : directory).filter((directory, index) => index === idx || directory !== action.replacement)
      };
    }
    // ── Input Needed ────────────────────────────────────────────────────
    case ActionType.SessionInputNeededSet: {
      const list = state.inputNeeded ?? [];
      const idx = list.findIndex((r) => r.id === action.request.id);
      const inputNeeded = idx < 0 ? [...list, action.request] : list.slice();
      if (idx >= 0) {
        inputNeeded[idx] = action.request;
      }
      return { ...state, inputNeeded, status: withInputNeededStatus(state.status, inputNeeded) };
    }
    case ActionType.SessionInputNeededRemoved: {
      const list = state.inputNeeded;
      if (!list) {
        return state;
      }
      const idx = list.findIndex((r) => r.id === action.id);
      if (idx < 0) {
        return state;
      }
      const remaining = list.slice();
      remaining.splice(idx, 1);
      const next = { ...state, status: withInputNeededStatus(state.status, remaining) };
      if (remaining.length > 0) {
        next.inputNeeded = remaining;
      } else {
        delete next.inputNeeded;
      }
      return next;
    }
    // ── Customizations ──────────────────────────────────────────────────
    case ActionType.SessionCustomizationsChanged:
      return { ...state, customizations: action.customizations };
    case ActionType.SessionCustomizationToggled: {
      const list = state.customizations;
      if (!list) {
        return state;
      }
      const topIdx = list.findIndex((c) => c.id === action.id);
      if (topIdx >= 0) {
        const updated = list.slice();
        updated[topIdx] = applyCustomizationEnablement(list[topIdx], action.enablement);
        return { ...state, customizations: updated };
      }
      for (let i = 0; i < list.length; i++) {
        const container = list[i];
        if (container.type === CustomizationType.McpServer) {
          continue;
        }
        const children = container.children;
        if (!children) {
          continue;
        }
        const childIdx = children.findIndex((c) => c.id === action.id);
        if (childIdx < 0) {
          continue;
        }
        const newChildren = children.slice();
        newChildren[childIdx] = applyCustomizationEnablement(children[childIdx], action.enablement);
        const updated = list.slice();
        updated[i] = { ...container, children: newChildren };
        return { ...state, customizations: updated };
      }
      return state;
    }
    case ActionType.SessionCustomizationUpdated: {
      const list = state.customizations ?? [];
      const idx = list.findIndex((c) => c.id === action.customization.id);
      if (idx < 0) {
        return { ...state, customizations: [...list, action.customization] };
      }
      const updated = [...list];
      updated[idx] = action.customization;
      return { ...state, customizations: updated };
    }
    case ActionType.SessionCustomizationRemoved: {
      const list = state.customizations;
      if (!list) {
        return state;
      }
      const topIdx = list.findIndex((c) => c.id === action.id);
      if (topIdx >= 0) {
        const updated2 = list.slice();
        updated2.splice(topIdx, 1);
        return { ...state, customizations: updated2 };
      }
      let changed = false;
      const updated = list.map((container) => {
        if (container.type === CustomizationType.McpServer) {
          return container;
        }
        const children = container.children;
        if (!children) {
          return container;
        }
        const childIdx = children.findIndex((c) => c.id === action.id);
        if (childIdx < 0) {
          return container;
        }
        changed = true;
        const newChildren = children.slice();
        newChildren.splice(childIdx, 1);
        return { ...container, children: newChildren };
      });
      if (!changed) {
        return state;
      }
      return { ...state, customizations: updated };
    }
    case ActionType.SessionMcpServerStateChanged: {
      return updateMcpServerCustomization(state, action.id, (entry) => ({
        ...entry,
        state: action.state,
        channel: action.channel
      }));
    }
    case ActionType.SessionMcpServerStartRequested: {
      return updateMcpServerCustomization(state, action.id, (entry) => ({
        ...entry,
        state: { kind: McpServerStatus.Starting },
        channel: void 0
      }));
    }
    case ActionType.SessionMcpServerStopRequested: {
      return updateMcpServerCustomization(state, action.id, (entry) => ({
        ...entry,
        state: { kind: McpServerStatus.Stopped },
        channel: void 0
      }));
    }
    default:
      softAssertNever(action, log);
      return state;
  }
}

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-terminal/state.js
var TerminalLifecycleStatus;
(function(TerminalLifecycleStatus2) {
  TerminalLifecycleStatus2["Running"] = "running";
  TerminalLifecycleStatus2["Exited"] = "exited";
})(TerminalLifecycleStatus || (TerminalLifecycleStatus = {}));
var TerminalClaimKind;
(function(TerminalClaimKind2) {
  TerminalClaimKind2["Client"] = "client";
  TerminalClaimKind2["Session"] = "session";
})(TerminalClaimKind || (TerminalClaimKind = {}));

// node_modules/@microsoft/agent-host-protocol/dist/ws/transport.js
var WebSocketTransport = class _WebSocketTransport {
  socket;
  inbox = [];
  waiters = [];
  closeInfo = null;
  error = null;
  closed = false;
  /**
   * Open a new WebSocket connection.
   *
   * Resolves once the socket emits `open`. Rejects with a
   * {@link TransportError} on early failure — either an `error` event or a
   * `close` event before `open`.
   */
  static connect(url, options = {}) {
    return new Promise((resolve, reject) => {
      const SocketCtor = globalThis.WebSocket;
      if (!SocketCtor) {
        reject(new TransportError("io", "global WebSocket is not available; install or polyfill it"));
        return;
      }
      let socket2;
      try {
        socket2 = options.protocols !== void 0 ? new SocketCtor(url, options.protocols) : new SocketCtor(url);
      } catch (err) {
        reject(new TransportError("io", `failed to construct WebSocket: ${err.message}`, { cause: err }));
        return;
      }
      const cleanup = () => {
        socket2.removeEventListener("open", onOpen);
        socket2.removeEventListener("error", onErrorBeforeOpen);
        socket2.removeEventListener("close", onCloseBeforeOpen);
      };
      const onOpen = () => {
        cleanup();
        resolve(new _WebSocketTransport(socket2));
      };
      const onErrorBeforeOpen = () => {
        cleanup();
        reject(new TransportError("io", "websocket failed to open"));
      };
      const onCloseBeforeOpen = (ev) => {
        cleanup();
        reject(new TransportError("closed", `websocket closed before open (code=${ev.code})`));
      };
      socket2.addEventListener("open", onOpen);
      socket2.addEventListener("error", onErrorBeforeOpen);
      socket2.addEventListener("close", onCloseBeforeOpen);
    });
  }
  /**
   * Wrap an already-open WebSocket. Use this when you need to control
   * the handshake (custom subprotocols, query params, an existing
   * connection from another library).
   *
   * The socket MUST already be in the `OPEN` state.
   */
  static fromSocket(socket2) {
    if (socket2.readyState !== socket2.OPEN) {
      throw new TransportError("io", "socket is not OPEN");
    }
    return new _WebSocketTransport(socket2);
  }
  constructor(socket2) {
    this.socket = socket2;
    socket2.binaryType = "arraybuffer";
    socket2.addEventListener("message", (ev) => {
      const data = ev.data;
      if (typeof data === "string") {
        this.deliver({ kind: "text", text: data });
      } else if (data instanceof ArrayBuffer) {
        this.deliver({ kind: "binary", data: new Uint8Array(data) });
      } else if (data instanceof Uint8Array) {
        this.deliver({ kind: "binary", data });
      } else {
        const err = new TransportError("protocol", "unsupported WebSocket message payload (expected string or ArrayBuffer)");
        this.error = err;
        this.drainWithError(err);
      }
    });
    socket2.addEventListener("error", () => {
      this.error = new TransportError("io", "websocket error");
      this.drainWithError(this.error);
    });
    socket2.addEventListener("close", (ev) => {
      this.closeInfo = { code: ev.code, reason: ev.reason, wasClean: ev.wasClean };
      this.closed = true;
      if (!ev.wasClean) {
        const err = new TransportError("closed", `websocket closed abnormally (code=${ev.code})`);
        this.error = err;
        this.drainWithError(err);
      } else {
        this.drainWithNull();
      }
    });
  }
  /** Bytes still queued in the underlying socket's send buffer. */
  get bufferedAmount() {
    return this.socket.bufferedAmount;
  }
  /**
   * Information about the most recent close, set once the socket emits
   * `close`. `null` while the connection is open.
   */
  get lastClose() {
    return this.closeInfo;
  }
  send(message) {
    if (this.closed)
      throw new TransportError("closed", "transport closed");
    if (this.error)
      throw this.error;
    const payload = typeof message === "string" ? message : encodeMessage(message);
    try {
      this.socket.send(payload);
    } catch (err) {
      throw new TransportError("io", `websocket send failed: ${err.message}`, { cause: err });
    }
  }
  recv() {
    if (this.error)
      return Promise.reject(this.error);
    if (this.inbox.length > 0) {
      const frame = this.inbox.shift() ?? null;
      return Promise.resolve(frame);
    }
    if (this.closed)
      return Promise.resolve(null);
    return new Promise((resolve, reject) => {
      this.waiters.push({ resolve, reject });
    });
  }
  close() {
    if (this.socket.readyState === this.socket.OPEN || this.socket.readyState === this.socket.CONNECTING) {
      try {
        this.socket.close();
      } catch {
      }
    }
    return Promise.resolve();
  }
  deliver(frame) {
    if (this.waiters.length > 0) {
      const w = this.waiters.shift();
      if (w)
        w.resolve(frame);
      return;
    }
    this.inbox.push(frame);
  }
  drainWithError(error) {
    const waiters = this.waiters;
    this.waiters = [];
    for (const w of waiters)
      w.reject(error);
  }
  drainWithNull() {
    const waiters = this.waiters;
    this.waiters = [];
    for (const w of waiters)
      w.resolve(null);
  }
};

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-root/state.js
var PolicyState;
(function(PolicyState2) {
  PolicyState2["Enabled"] = "enabled";
  PolicyState2["Disabled"] = "disabled";
  PolicyState2["Unconfigured"] = "unconfigured";
})(PolicyState || (PolicyState = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-chat/state.js
var ChatOriginKind;
(function(ChatOriginKind2) {
  ChatOriginKind2["User"] = "user";
  ChatOriginKind2["Fork"] = "fork";
  ChatOriginKind2["SideChat"] = "sideChat";
  ChatOriginKind2["Tool"] = "tool";
})(ChatOriginKind || (ChatOriginKind = {}));
var ChatInteractivity;
(function(ChatInteractivity2) {
  ChatInteractivity2["Full"] = "full";
  ChatInteractivity2["ReadOnly"] = "read-only";
  ChatInteractivity2["Hidden"] = "hidden";
})(ChatInteractivity || (ChatInteractivity = {}));
var PendingMessageKind;
(function(PendingMessageKind2) {
  PendingMessageKind2["Steering"] = "steering";
  PendingMessageKind2["Queued"] = "queued";
})(PendingMessageKind || (PendingMessageKind = {}));
var ChatInputResponseKind;
(function(ChatInputResponseKind2) {
  ChatInputResponseKind2["Accept"] = "accept";
  ChatInputResponseKind2["Decline"] = "decline";
  ChatInputResponseKind2["Cancel"] = "cancel";
})(ChatInputResponseKind || (ChatInputResponseKind = {}));
var ChatInputQuestionKind;
(function(ChatInputQuestionKind2) {
  ChatInputQuestionKind2["Text"] = "text";
  ChatInputQuestionKind2["Number"] = "number";
  ChatInputQuestionKind2["Integer"] = "integer";
  ChatInputQuestionKind2["Boolean"] = "boolean";
  ChatInputQuestionKind2["SingleSelect"] = "single-select";
  ChatInputQuestionKind2["MultiSelect"] = "multi-select";
})(ChatInputQuestionKind || (ChatInputQuestionKind = {}));
var ChatInputAnswerValueKind;
(function(ChatInputAnswerValueKind2) {
  ChatInputAnswerValueKind2["Text"] = "text";
  ChatInputAnswerValueKind2["Number"] = "number";
  ChatInputAnswerValueKind2["Boolean"] = "boolean";
  ChatInputAnswerValueKind2["Selected"] = "selected";
  ChatInputAnswerValueKind2["SelectedMany"] = "selected-many";
})(ChatInputAnswerValueKind || (ChatInputAnswerValueKind = {}));
var ChatInputAnswerState;
(function(ChatInputAnswerState2) {
  ChatInputAnswerState2["Draft"] = "draft";
  ChatInputAnswerState2["Submitted"] = "submitted";
  ChatInputAnswerState2["Skipped"] = "skipped";
})(ChatInputAnswerState || (ChatInputAnswerState = {}));
var TurnState;
(function(TurnState2) {
  TurnState2["Complete"] = "complete";
  TurnState2["Cancelled"] = "cancelled";
  TurnState2["Error"] = "error";
})(TurnState || (TurnState = {}));
var MessageAttachmentKind;
(function(MessageAttachmentKind2) {
  MessageAttachmentKind2["Simple"] = "simple";
  MessageAttachmentKind2["EmbeddedResource"] = "embeddedResource";
  MessageAttachmentKind2["Resource"] = "resource";
  MessageAttachmentKind2["Annotations"] = "annotations";
  MessageAttachmentKind2["Chat"] = "chat";
})(MessageAttachmentKind || (MessageAttachmentKind = {}));
var MessageKind;
(function(MessageKind2) {
  MessageKind2["User"] = "user";
  MessageKind2["Agent"] = "agent";
  MessageKind2["Tool"] = "tool";
  MessageKind2["Automation"] = "automation";
  MessageKind2["SystemNotification"] = "systemNotification";
})(MessageKind || (MessageKind = {}));
var ResponsePartKind;
(function(ResponsePartKind2) {
  ResponsePartKind2["Markdown"] = "markdown";
  ResponsePartKind2["ContentRef"] = "contentRef";
  ResponsePartKind2["ToolCall"] = "toolCall";
  ResponsePartKind2["Reasoning"] = "reasoning";
  ResponsePartKind2["SystemNotification"] = "systemNotification";
  ResponsePartKind2["InputRequest"] = "inputRequest";
  ResponsePartKind2["Error"] = "error";
})(ResponsePartKind || (ResponsePartKind = {}));
var ToolCallStatus;
(function(ToolCallStatus2) {
  ToolCallStatus2["Streaming"] = "streaming";
  ToolCallStatus2["PendingConfirmation"] = "pending-confirmation";
  ToolCallStatus2["Running"] = "running";
  ToolCallStatus2["AuthRequired"] = "auth-required";
  ToolCallStatus2["PendingResultConfirmation"] = "pending-result-confirmation";
  ToolCallStatus2["Completed"] = "completed";
  ToolCallStatus2["Cancelled"] = "cancelled";
})(ToolCallStatus || (ToolCallStatus = {}));
var ToolCallConfirmationReason;
(function(ToolCallConfirmationReason2) {
  ToolCallConfirmationReason2["NotNeeded"] = "not-needed";
  ToolCallConfirmationReason2["UserAction"] = "user-action";
  ToolCallConfirmationReason2["Setting"] = "setting";
})(ToolCallConfirmationReason || (ToolCallConfirmationReason = {}));
var ToolCallRiskAssessmentKind;
(function(ToolCallRiskAssessmentKind2) {
  ToolCallRiskAssessmentKind2["Judge"] = "judge";
})(ToolCallRiskAssessmentKind || (ToolCallRiskAssessmentKind = {}));
var ToolCallRiskAssessmentStatus;
(function(ToolCallRiskAssessmentStatus2) {
  ToolCallRiskAssessmentStatus2["Loading"] = "loading";
  ToolCallRiskAssessmentStatus2["Complete"] = "complete";
})(ToolCallRiskAssessmentStatus || (ToolCallRiskAssessmentStatus = {}));
var ToolCallCancellationReason;
(function(ToolCallCancellationReason2) {
  ToolCallCancellationReason2["Denied"] = "denied";
  ToolCallCancellationReason2["Skipped"] = "skipped";
  ToolCallCancellationReason2["ResultDenied"] = "result-denied";
})(ToolCallCancellationReason || (ToolCallCancellationReason = {}));
var ConfirmationOptionKind;
(function(ConfirmationOptionKind2) {
  ConfirmationOptionKind2["Approve"] = "approve";
  ConfirmationOptionKind2["Deny"] = "deny";
})(ConfirmationOptionKind || (ConfirmationOptionKind = {}));
var ToolCallContributorKind;
(function(ToolCallContributorKind2) {
  ToolCallContributorKind2["Client"] = "client";
  ToolCallContributorKind2["MCP"] = "mcp";
})(ToolCallContributorKind || (ToolCallContributorKind = {}));
var ToolResultContentType;
(function(ToolResultContentType2) {
  ToolResultContentType2["Text"] = "text";
  ToolResultContentType2["EmbeddedResource"] = "embeddedResource";
  ToolResultContentType2["Resource"] = "resource";
  ToolResultContentType2["FileEdit"] = "fileEdit";
  ToolResultContentType2["Terminal"] = "terminal";
  ToolResultContentType2["Subagent"] = "subagent";
})(ToolResultContentType || (ToolResultContentType = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-resource-watch/state.js
var ResourceChangeType;
(function(ResourceChangeType2) {
  ResourceChangeType2["Added"] = "added";
  ResourceChangeType2["Updated"] = "updated";
  ResourceChangeType2["Deleted"] = "deleted";
})(ResourceChangeType || (ResourceChangeType = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-automation/state.js
var AutomationOperation;
(function(AutomationOperation2) {
  AutomationOperation2["Update"] = "update";
  AutomationOperation2["Remove"] = "remove";
  AutomationOperation2["Run"] = "run";
})(AutomationOperation || (AutomationOperation = {}));
var AutomationMisfirePolicy;
(function(AutomationMisfirePolicy2) {
  AutomationMisfirePolicy2["Skip"] = "skip";
  AutomationMisfirePolicy2["RunOnce"] = "runOnce";
})(AutomationMisfirePolicy || (AutomationMisfirePolicy = {}));
var AutomationTriggerKind;
(function(AutomationTriggerKind2) {
  AutomationTriggerKind2["Schedule"] = "schedule";
  AutomationTriggerKind2["Event"] = "event";
})(AutomationTriggerKind || (AutomationTriggerKind = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-automation-run/state.js
var AutomationRunStatus;
(function(AutomationRunStatus2) {
  AutomationRunStatus2["Pending"] = "pending";
  AutomationRunStatus2["Running"] = "running";
  AutomationRunStatus2["Completed"] = "completed";
  AutomationRunStatus2["Failed"] = "failed";
  AutomationRunStatus2["Cancelled"] = "cancelled";
})(AutomationRunStatus || (AutomationRunStatus = {}));
var AutomationRunOriginKind;
(function(AutomationRunOriginKind2) {
  AutomationRunOriginKind2["Manual"] = "manual";
  AutomationRunOriginKind2["Trigger"] = "trigger";
})(AutomationRunOriginKind || (AutomationRunOriginKind = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/common/commands.js
var ReconnectResultType;
(function(ReconnectResultType2) {
  ReconnectResultType2["Replay"] = "replay";
  ReconnectResultType2["Snapshot"] = "snapshot";
})(ReconnectResultType || (ReconnectResultType = {}));
var ContentEncoding;
(function(ContentEncoding2) {
  ContentEncoding2["Base64"] = "base64";
  ContentEncoding2["Utf8"] = "utf-8";
})(ContentEncoding || (ContentEncoding = {}));
var ResourceWriteMode;
(function(ResourceWriteMode2) {
  ResourceWriteMode2["Truncate"] = "truncate";
  ResourceWriteMode2["Append"] = "append";
  ResourceWriteMode2["Insert"] = "insert";
})(ResourceWriteMode || (ResourceWriteMode = {}));
var ResourceType;
(function(ResourceType2) {
  ResourceType2["File"] = "file";
  ResourceType2["Directory"] = "directory";
  ResourceType2["Symlink"] = "symlink";
})(ResourceType || (ResourceType = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-session/commands.js
var CompletionItemKind;
(function(CompletionItemKind2) {
  CompletionItemKind2["UserMessage"] = "userMessage";
})(CompletionItemKind || (CompletionItemKind = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-chat/commands.js
var ChatSourceKind;
(function(ChatSourceKind2) {
  ChatSourceKind2["Fork"] = "fork";
  ChatSourceKind2["SideChat"] = "sideChat";
})(ChatSourceKind || (ChatSourceKind = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-changeset/commands.js
var ChangesetOperationTargetKind;
(function(ChangesetOperationTargetKind2) {
  ChangesetOperationTargetKind2["Resource"] = "resource";
  ChangesetOperationTargetKind2["Range"] = "range";
})(ChangesetOperationTargetKind || (ChangesetOperationTargetKind = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/common/notifications.js
var AuthRequiredReason;
(function(AuthRequiredReason2) {
  AuthRequiredReason2["Required"] = "required";
  AuthRequiredReason2["Expired"] = "expired";
})(AuthRequiredReason || (AuthRequiredReason = {}));

// node_modules/@microsoft/agent-host-protocol/dist/types/version/registry.js
var SUPPORTED_PROTOCOL_VERSIONS = Object.freeze([
  "0.9.0",
  "0.8.0",
  "0.7.0",
  "0.6.0",
  "0.5.2",
  "0.5.1"
]);
var ACTION_INTRODUCED_IN = {
  [ActionType.RootAgentsChanged]: "0.1.0",
  [ActionType.RootActiveSessionsChanged]: "0.1.0",
  [ActionType.SessionReady]: "0.1.0",
  [ActionType.SessionCreationFailed]: "0.1.0",
  [ActionType.SessionChatAdded]: "0.4.0",
  [ActionType.SessionChatRemoved]: "0.4.0",
  [ActionType.SessionChatUpdated]: "0.4.0",
  [ActionType.SessionDefaultChatChanged]: "0.4.0",
  [ActionType.SessionTitleChanged]: "0.1.0",
  [ActionType.SessionServerToolsChanged]: "0.1.0",
  [ActionType.SessionActiveClientSet]: "0.5.0",
  [ActionType.SessionActiveClientRemoved]: "0.5.0",
  [ActionType.SessionWorkingDirectorySet]: "0.7.0",
  [ActionType.SessionWorkingDirectoryRemoved]: "0.7.0",
  [ActionType.SessionWorkingDirectoryReplaced]: "0.8.0",
  [ActionType.SessionInputNeededSet]: "0.5.1",
  [ActionType.SessionInputNeededRemoved]: "0.5.1",
  [ActionType.SessionCustomizationsChanged]: "0.1.0",
  [ActionType.SessionCustomizationToggled]: "0.1.0",
  [ActionType.SessionCustomizationUpdated]: "0.1.0",
  [ActionType.SessionCustomizationRemoved]: "0.2.0",
  [ActionType.SessionMcpServerStateChanged]: "0.3.0",
  [ActionType.SessionMcpServerStartRequested]: "0.5.2",
  [ActionType.SessionMcpServerStopRequested]: "0.5.2",
  [ActionType.SessionIsReadChanged]: "0.1.0",
  [ActionType.SessionIsArchivedChanged]: "0.1.0",
  [ActionType.SessionActivityChanged]: "0.1.0",
  [ActionType.SessionChangesetsChanged]: "0.2.0",
  [ActionType.SessionConfigChanged]: "0.1.0",
  [ActionType.SessionMetaChanged]: "0.1.0",
  [ActionType.ChatTurnStarted]: "0.4.0",
  [ActionType.ChatDelta]: "0.4.0",
  [ActionType.ChatResponsePart]: "0.4.0",
  [ActionType.ChatToolCallStart]: "0.4.0",
  [ActionType.ChatToolCallDelta]: "0.4.0",
  [ActionType.ChatToolCallReady]: "0.4.0",
  [ActionType.ChatToolCallConfirmed]: "0.4.0",
  [ActionType.ChatToolCallComplete]: "0.4.0",
  [ActionType.ChatToolCallResultConfirmed]: "0.4.0",
  [ActionType.ChatToolCallContentChanged]: "0.4.0",
  [ActionType.ChatToolCallAuthRequired]: "0.6.0",
  [ActionType.ChatToolCallAuthResolved]: "0.6.0",
  [ActionType.ChatTurnComplete]: "0.4.0",
  [ActionType.ChatTurnCancelled]: "0.4.0",
  [ActionType.ChatError]: "0.4.0",
  [ActionType.ChatTurnResume]: "0.9.0",
  [ActionType.ChatActivityChanged]: "0.5.0",
  [ActionType.ChatWorkingDirectorySet]: "0.7.0",
  [ActionType.ChatWorkingDirectoryRemoved]: "0.7.0",
  [ActionType.ChatUsage]: "0.4.0",
  [ActionType.ChatReasoning]: "0.4.0",
  [ActionType.ChatPendingMessageSet]: "0.4.0",
  [ActionType.ChatPendingMessageRemoved]: "0.4.0",
  [ActionType.ChatQueuedMessagesReordered]: "0.4.0",
  [ActionType.ChatDraftChanged]: "0.5.0",
  [ActionType.ChatInputRequested]: "0.4.0",
  [ActionType.ChatInputAnswerChanged]: "0.4.0",
  [ActionType.ChatInputCompleted]: "0.4.0",
  [ActionType.ChatTruncated]: "0.4.0",
  [ActionType.ChatTurnsLoaded]: "0.5.1",
  [ActionType.ChangesetStatusChanged]: "0.2.0",
  [ActionType.ChangesetFileSet]: "0.2.0",
  [ActionType.ChangesetFileRemoved]: "0.2.0",
  [ActionType.ChangesetFilesReviewChanged]: "0.6.0",
  [ActionType.ChangesetContentChanged]: "0.4.0",
  [ActionType.ChangesetOperationsChanged]: "0.2.0",
  [ActionType.ChangesetOperationStatusChanged]: "0.3.0",
  [ActionType.ChangesetCleared]: "0.2.0",
  [ActionType.AnnotationsSet]: "0.4.0",
  [ActionType.AnnotationsUpdated]: "0.4.0",
  [ActionType.AnnotationsRemoved]: "0.4.0",
  [ActionType.AnnotationsEntrySet]: "0.4.0",
  [ActionType.AnnotationsEntryRemoved]: "0.4.0",
  [ActionType.RootTerminalsChanged]: "0.1.0",
  [ActionType.RootConfigChanged]: "0.1.0",
  [ActionType.TerminalData]: "0.1.0",
  [ActionType.TerminalInput]: "0.1.0",
  [ActionType.TerminalResized]: "0.1.0",
  [ActionType.TerminalClaimed]: "0.1.0",
  [ActionType.TerminalTitleChanged]: "0.1.0",
  [ActionType.TerminalCwdChanged]: "0.1.0",
  [ActionType.TerminalExited]: "0.1.0",
  [ActionType.TerminalCleared]: "0.1.0",
  [ActionType.TerminalCommandDetectionAvailable]: "0.1.0",
  [ActionType.TerminalCommandExecuted]: "0.1.0",
  [ActionType.TerminalCommandFinished]: "0.1.0",
  [ActionType.ResourceWatchChanged]: "0.2.0",
  [ActionType.AutomationCreateRequested]: "0.8.0",
  [ActionType.AutomationUpdateRequested]: "0.8.0",
  [ActionType.AutomationSet]: "0.8.0",
  [ActionType.AutomationRemoved]: "0.8.0",
  [ActionType.AutomationRunLifecycleChanged]: "0.8.0",
  [ActionType.AutomationRunSessionSet]: "0.8.0",
  [ActionType.AutomationRunSessionRemoved]: "0.8.0",
  [ActionType.AutomationRunPrimarySessionChanged]: "0.8.0",
  [ActionType.AutomationRunCancelRequested]: "0.8.0"
};

// node_modules/@microsoft/agent-host-protocol/dist/types/common/timestamps.js
function addMillisecondsToTimestamp(timestamp, duration) {
  return new Date(Date.parse(timestamp) + duration).toISOString();
}

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-chat/reducer.js
function tcBase(tc) {
  return {
    toolCallId: tc.toolCallId,
    toolName: tc.toolName,
    displayName: tc.displayName,
    intention: tc.intention,
    contributor: tc.contributor,
    _meta: tc._meta
  };
}
function tcBaseWithMeta(tc, meta) {
  return {
    ...tcBase(tc),
    _meta: meta ?? tc._meta
  };
}
function refineToolCallContributor(current, next, log) {
  if (!next) {
    return current;
  }
  if (current?.kind === ToolCallContributorKind.Client) {
    if (next.kind === ToolCallContributorKind.Client && next.clientId === current.clientId) {
      return next;
    }
    log?.(`Ignoring contributor change for client tool call from '${current.clientId}'`);
    return current;
  }
  if (next.kind === ToolCallContributorKind.Client) {
    log?.(`Ignoring late client contributor '${next.clientId}' because client execution ownership must be established at tool call start`);
    return current;
  }
  return next;
}
function resolveSelectedOption(options, id) {
  if (!id || !options) {
    return void 0;
  }
  return options.find((o) => o.id === id);
}
function hasBlockingToolCall(state) {
  if (!state.activeTurn) {
    return false;
  }
  return state.activeTurn.responseParts.some((part) => part.kind === ResponsePartKind.ToolCall && (part.toolCall.status === ToolCallStatus.PendingConfirmation || part.toolCall.status === ToolCallStatus.PendingResultConfirmation || part.toolCall.status === ToolCallStatus.AuthRequired));
}
function hasOpenInputRequest(state) {
  return state.activeTurn?.responseParts.some((part) => part.kind === ResponsePartKind.InputRequest && part.response === void 0) ?? false;
}
function findOpenInputRequestPart(responseParts, requestId) {
  const index = responseParts.findIndex((part2) => part2.kind === ResponsePartKind.InputRequest && part2.response === void 0 && part2.request.id === requestId);
  if (index < 0) {
    return void 0;
  }
  const part = responseParts[index];
  return part.kind === ResponsePartKind.InputRequest ? { index, part } : void 0;
}
function hasResumableError(turn) {
  const part = turn.responseParts[turn.responseParts.length - 1];
  return part?.kind === ResponsePartKind.Error && part.resumable === true;
}
function isErrorResponsePart(part) {
  return part.kind === ResponsePartKind.Error;
}
var STATUS_ACTIVITY_MASK2 = (1 << 5) - 1;
function withStatusFlag2(status, flag, set) {
  return set ? status | flag : status & ~flag;
}
function summaryStatus(state, terminalStatus) {
  let activity;
  if (terminalStatus) {
    activity = terminalStatus;
  } else if (hasOpenInputRequest(state) || hasBlockingToolCall(state)) {
    activity = SessionStatus.InputNeeded;
  } else if (state.activeTurn) {
    activity = SessionStatus.InProgress;
  } else {
    activity = SessionStatus.Idle;
  }
  return state.status & ~STATUS_ACTIVITY_MASK2 | activity;
}
function refreshSummaryStatus(state) {
  const status = summaryStatus(state);
  if (status === state.status) {
    return state;
  }
  return { ...state, status };
}
function endTurn(state, turnId, turnState, duration, terminalStatus, errorPart) {
  if (!state.activeTurn || state.activeTurn.id !== turnId) {
    return state;
  }
  const active = state.activeTurn;
  const responseParts = active.responseParts.map((part) => {
    if (part.kind !== ResponsePartKind.ToolCall) {
      return part;
    }
    const tc = part.toolCall;
    if (tc.status === ToolCallStatus.Completed || tc.status === ToolCallStatus.Cancelled) {
      return part;
    }
    return {
      kind: ResponsePartKind.ToolCall,
      toolCall: {
        status: ToolCallStatus.Cancelled,
        ...tcBase(tc),
        invocationMessage: tc.status === ToolCallStatus.Streaming ? tc.invocationMessage ?? "" : tc.invocationMessage,
        toolInput: tc.status === ToolCallStatus.Streaming ? void 0 : tc.toolInput,
        reason: ToolCallCancellationReason.Skipped
      }
    };
  });
  if (errorPart) {
    responseParts.push(errorPart);
  }
  const turn = {
    id: active.id,
    startedAt: active.startedAt,
    // Defensive clamp: the duration is producer-supplied and opaque to this
    // reducer, but a negative value would be nonsensical to display.
    duration: Math.max(0, duration),
    message: active.message,
    responseParts,
    usage: active.usage,
    state: turnState
  };
  const next = {
    ...state,
    turns: [...state.turns, turn],
    activeTurn: void 0,
    modifiedAt: addMillisecondsToTimestamp(active.startedAt, turn.duration ?? 0)
  };
  return {
    ...next,
    status: summaryStatus(next, terminalStatus)
  };
}
function upsertInputRequestPart(state, request) {
  const activeTurn = state.activeTurn;
  if (!activeTurn) {
    return state;
  }
  const existing = findOpenInputRequestPart(activeTurn.responseParts, request.id);
  const responseParts = [...activeTurn.responseParts];
  const part = {
    kind: ResponsePartKind.InputRequest,
    request
  };
  if (existing) {
    part.request = {
      ...request,
      answers: request.answers ?? existing.part.request.answers
    };
    responseParts[existing.index] = part;
  } else {
    responseParts.push(part);
  }
  const next = {
    ...state,
    activeTurn: {
      ...activeTurn,
      responseParts
    }
  };
  return { ...next, status: withStatusFlag2(summaryStatus(next), SessionStatus.IsRead, false) };
}
function updateToolCallInParts(state, turnId, toolCallId, updater) {
  const activeTurn = state.activeTurn;
  if (!activeTurn || activeTurn.id !== turnId) {
    return state;
  }
  let found = false;
  const responseParts = activeTurn.responseParts.map((part) => {
    if (part.kind === ResponsePartKind.ToolCall && part.toolCall.toolCallId === toolCallId) {
      const updated = updater(part.toolCall);
      if (updated === part.toolCall) {
        return part;
      }
      found = true;
      return { ...part, toolCall: updated };
    }
    return part;
  });
  if (!found) {
    return state;
  }
  return {
    ...state,
    activeTurn: { ...activeTurn, responseParts }
  };
}
function updateResponsePart(state, turnId, partId, updater) {
  const activeTurn = state.activeTurn;
  if (!activeTurn || activeTurn.id !== turnId) {
    return state;
  }
  let found = false;
  const responseParts = activeTurn.responseParts.map((part) => {
    if (!found) {
      const id = part.kind === ResponsePartKind.ToolCall ? part.toolCall.toolCallId : "id" in part ? part.id : void 0;
      if (id === partId) {
        found = true;
        return updater(part);
      }
    }
    return part;
  });
  if (!found) {
    return state;
  }
  return {
    ...state,
    activeTurn: { ...activeTurn, responseParts }
  };
}
function chatReducer(state, action, log) {
  switch (action.type) {
    // ── Turn Lifecycle ────────────────────────────────────────────────────
    case ActionType.ChatTurnStarted: {
      let next = {
        ...state,
        activeTurn: {
          id: action.turnId,
          startedAt: action.startedAt,
          message: action.message,
          responseParts: [],
          usage: void 0
        }
      };
      next = {
        ...next,
        status: withStatusFlag2(summaryStatus(next), SessionStatus.IsRead, false),
        modifiedAt: action.startedAt
      };
      if (action.queuedMessageId) {
        if (next.steeringMessage?.id === action.queuedMessageId) {
          next = { ...next, steeringMessage: void 0 };
        }
        if (next.queuedMessages) {
          const filtered = next.queuedMessages.filter((m) => m.id !== action.queuedMessageId);
          next = { ...next, queuedMessages: filtered.length > 0 ? filtered : void 0 };
        }
      }
      return next;
    }
    case ActionType.ChatDelta:
      return updateResponsePart(state, action.turnId, action.partId, (part) => {
        if (part.kind === ResponsePartKind.Markdown) {
          return { ...part, content: part.content + action.content };
        }
        return part;
      });
    case ActionType.ChatResponsePart:
      if (!state.activeTurn || state.activeTurn.id !== action.turnId) {
        return state;
      }
      if (isErrorResponsePart(action.part)) {
        return state;
      }
      return {
        ...state,
        activeTurn: {
          ...state.activeTurn,
          responseParts: [...state.activeTurn.responseParts, action.part]
        }
      };
    case ActionType.ChatTurnComplete:
      return endTurn(state, action.turnId, TurnState.Complete, action.duration);
    case ActionType.ChatTurnCancelled:
      return endTurn(state, action.turnId, TurnState.Cancelled, action.duration);
    case ActionType.ChatError:
      return endTurn(state, action.turnId, TurnState.Error, action.duration, SessionStatus.Error, action.part);
    case ActionType.ChatTurnResume: {
      if (state.activeTurn) {
        return state;
      }
      const turnIndex = state.turns.length - 1;
      const turn = state.turns[turnIndex];
      if (!turn || turn.id !== action.turnId || turn.state !== TurnState.Error || !hasResumableError(turn)) {
        return state;
      }
      const turns = state.turns.slice();
      turns.splice(turnIndex, 1);
      const next = {
        ...state,
        turns,
        activeTurn: {
          id: turn.id,
          startedAt: turn.startedAt ?? state.modifiedAt,
          message: turn.message,
          responseParts: turn.responseParts,
          usage: turn.usage
        }
      };
      return {
        ...next,
        status: withStatusFlag2(summaryStatus(next), SessionStatus.IsRead, false)
      };
    }
    case ActionType.ChatActivityChanged:
      return { ...state, activity: action.activity };
    // ── Working Directories ───────────────────────────────────────────────
    case ActionType.ChatWorkingDirectorySet: {
      const list = state.workingDirectories ?? [];
      if (list.includes(action.directory)) {
        return state;
      }
      return { ...state, workingDirectories: [...list, action.directory] };
    }
    case ActionType.ChatWorkingDirectoryRemoved: {
      const list = state.workingDirectories;
      if (!list) {
        return state;
      }
      const idx = list.indexOf(action.directory);
      if (idx < 0) {
        return state;
      }
      const updated = list.slice();
      updated.splice(idx, 1);
      return { ...state, workingDirectories: updated };
    }
    // ── Tool Call State Machine ───────────────────────────────────────────
    case ActionType.ChatToolCallStart:
      if (!state.activeTurn || state.activeTurn.id !== action.turnId) {
        return state;
      }
      return {
        ...state,
        activeTurn: {
          ...state.activeTurn,
          responseParts: [
            ...state.activeTurn.responseParts,
            {
              kind: ResponsePartKind.ToolCall,
              toolCall: {
                toolCallId: action.toolCallId,
                toolName: action.toolName,
                displayName: action.displayName,
                intention: action.intention,
                contributor: action.contributor,
                _meta: action._meta,
                status: ToolCallStatus.Streaming
              }
            }
          ]
        }
      };
    case ActionType.ChatToolCallDelta:
      return updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.Streaming) {
          return tc;
        }
        return {
          ...tc,
          ...action._meta !== void 0 ? { _meta: action._meta } : {},
          ...action.content !== void 0 ? { partialInput: (tc.partialInput ?? "") + action.content } : {},
          invocationMessage: action.invocationMessage ?? tc.invocationMessage
        };
      });
    case ActionType.ChatToolCallReady:
      return refreshSummaryStatus(updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.Streaming && tc.status !== ToolCallStatus.Running && tc.status !== ToolCallStatus.PendingConfirmation) {
          return tc;
        }
        const base = {
          ...tcBaseWithMeta(tc, action._meta),
          contributor: refineToolCallContributor(tc.contributor, action.contributor, log),
          intention: action.intention ?? tc.intention
        };
        const toolInput = action.toolInput ?? (tc.status === ToolCallStatus.Streaming ? void 0 : tc.toolInput);
        if (action.confirmed) {
          return {
            status: ToolCallStatus.Running,
            ...base,
            invocationMessage: action.invocationMessage,
            toolInput,
            confirmed: action.confirmed
          };
        }
        const pending = tc.status === ToolCallStatus.PendingConfirmation ? tc : void 0;
        const options = action.options ?? pending?.options;
        return {
          status: ToolCallStatus.PendingConfirmation,
          ...base,
          invocationMessage: action.invocationMessage,
          toolInput,
          confirmationTitle: action.confirmationTitle ?? pending?.confirmationTitle,
          riskAssessment: action.riskAssessment ?? pending?.riskAssessment,
          edits: action.edits ?? pending?.edits,
          editable: action.editable ?? pending?.editable,
          ...options ? { options } : {}
        };
      }));
    case ActionType.ChatToolCallConfirmed:
      return refreshSummaryStatus(updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.PendingConfirmation) {
          return tc;
        }
        const base = tcBaseWithMeta(tc, action._meta);
        const selectedOption = resolveSelectedOption(tc.options, action.selectedOptionId);
        if (action.approved) {
          const toolInput = action.editedToolInput !== void 0 && typeof tc.toolInput === "string" ? action.editedToolInput : tc.toolInput;
          return {
            status: ToolCallStatus.Running,
            ...base,
            invocationMessage: tc.invocationMessage,
            toolInput,
            confirmed: action.confirmed,
            ...selectedOption ? { selectedOption } : {}
          };
        }
        return {
          status: ToolCallStatus.Cancelled,
          ...base,
          invocationMessage: tc.invocationMessage,
          toolInput: tc.toolInput,
          reason: action.reason,
          reasonMessage: action.reasonMessage,
          userSuggestion: action.userSuggestion,
          ...selectedOption ? { selectedOption } : {}
        };
      }));
    case ActionType.ChatToolCallComplete:
      return refreshSummaryStatus(updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.Running && tc.status !== ToolCallStatus.PendingConfirmation && tc.status !== ToolCallStatus.AuthRequired) {
          return tc;
        }
        if (tc.status === ToolCallStatus.AuthRequired && action.result.success) {
          return tc;
        }
        const base = tcBaseWithMeta(tc, action._meta);
        const confirmed = tc.status === ToolCallStatus.Running || tc.status === ToolCallStatus.AuthRequired ? tc.confirmed : ToolCallConfirmationReason.NotNeeded;
        const selectedOption = tc.status === ToolCallStatus.Running || tc.status === ToolCallStatus.AuthRequired ? tc.selectedOption : void 0;
        const preAuthContent = tc.status === ToolCallStatus.AuthRequired ? tc.content : void 0;
        if (action.requiresResultConfirmation && tc.status !== ToolCallStatus.AuthRequired) {
          return {
            status: ToolCallStatus.PendingResultConfirmation,
            ...base,
            invocationMessage: tc.invocationMessage,
            toolInput: tc.toolInput,
            confirmed,
            ...selectedOption ? { selectedOption } : {},
            ...preAuthContent ? { content: preAuthContent } : {},
            ...action.result
          };
        }
        return {
          status: ToolCallStatus.Completed,
          ...base,
          invocationMessage: tc.invocationMessage,
          toolInput: tc.toolInput,
          confirmed,
          ...selectedOption ? { selectedOption } : {},
          ...preAuthContent ? { content: preAuthContent } : {},
          ...action.result
        };
      }));
    case ActionType.ChatToolCallResultConfirmed:
      return refreshSummaryStatus(updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.PendingResultConfirmation) {
          return tc;
        }
        const base = tcBaseWithMeta(tc, action._meta);
        if (action.approved) {
          return {
            status: ToolCallStatus.Completed,
            ...base,
            invocationMessage: tc.invocationMessage,
            toolInput: tc.toolInput,
            confirmed: tc.confirmed,
            ...tc.selectedOption ? { selectedOption: tc.selectedOption } : {},
            success: tc.success,
            pastTenseMessage: tc.pastTenseMessage,
            content: tc.content,
            structuredContent: tc.structuredContent,
            error: tc.error
          };
        }
        return {
          status: ToolCallStatus.Cancelled,
          ...base,
          invocationMessage: tc.invocationMessage,
          toolInput: tc.toolInput,
          reason: ToolCallCancellationReason.ResultDenied,
          ...tc.selectedOption ? { selectedOption: tc.selectedOption } : {}
        };
      }));
    case ActionType.ChatToolCallContentChanged:
      return updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.Running) {
          return tc;
        }
        return {
          ...tc,
          ...action._meta !== void 0 ? { _meta: action._meta } : {},
          content: action.content
        };
      });
    case ActionType.ChatToolCallAuthRequired:
      return refreshSummaryStatus(updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.Running) {
          return tc;
        }
        if (!tc.contributor || tc.contributor.kind !== ToolCallContributorKind.MCP) {
          return tc;
        }
        const base = tcBaseWithMeta(tc, action._meta);
        return {
          status: ToolCallStatus.AuthRequired,
          ...base,
          contributor: tc.contributor,
          invocationMessage: tc.invocationMessage,
          toolInput: tc.toolInput,
          confirmed: tc.confirmed,
          ...tc.selectedOption ? { selectedOption: tc.selectedOption } : {},
          ...tc.content ? { content: tc.content } : {},
          auth: action.auth
        };
      }));
    case ActionType.ChatToolCallAuthResolved:
      return refreshSummaryStatus(updateToolCallInParts(state, action.turnId, action.toolCallId, (tc) => {
        if (tc.status !== ToolCallStatus.AuthRequired) {
          return tc;
        }
        const base = tcBaseWithMeta(tc, action._meta);
        return {
          status: ToolCallStatus.Running,
          ...base,
          invocationMessage: tc.invocationMessage,
          toolInput: tc.toolInput,
          confirmed: tc.confirmed,
          ...tc.selectedOption ? { selectedOption: tc.selectedOption } : {},
          ...tc.content ? { content: tc.content } : {}
        };
      }));
    case ActionType.ChatUsage:
      if (!state.activeTurn || state.activeTurn.id !== action.turnId) {
        return state;
      }
      return {
        ...state,
        activeTurn: { ...state.activeTurn, usage: action.usage }
      };
    case ActionType.ChatReasoning:
      return updateResponsePart(state, action.turnId, action.partId, (part) => {
        if (part.kind === ResponsePartKind.Reasoning) {
          return { ...part, content: part.content + action.content };
        }
        return part;
      });
    // ── Truncation ────────────────────────────────────────────────────────
    case ActionType.ChatTruncated: {
      let turns;
      if (action.turnId === void 0) {
        turns = [];
      } else {
        const idx = state.turns.findIndex((t) => t.id === action.turnId);
        if (idx < 0) {
          return state;
        }
        turns = state.turns.slice(0, idx + 1);
      }
      const next = {
        ...state,
        turns,
        activeTurn: void 0
      };
      if (action.turnId === void 0) {
        delete next.turnsNextCursor;
      }
      return {
        ...next,
        status: summaryStatus(next)
      };
    }
    case ActionType.ChatTurnsLoaded: {
      const existingIds = new Set(state.turns.map((turn) => turn.id));
      const olderTurns = action.turns.filter((turn) => !existingIds.has(turn.id));
      return {
        ...state,
        turns: [...olderTurns, ...state.turns],
        turnsNextCursor: action.turnsNextCursor
      };
    }
    // ── Session Input Requests ─────────────────────────────────────────────
    case ActionType.ChatInputRequested:
      return upsertInputRequestPart(state, action.request);
    case ActionType.ChatInputAnswerChanged: {
      const activeTurn = state.activeTurn;
      const existing = activeTurn ? findOpenInputRequestPart(activeTurn.responseParts, action.requestId) : void 0;
      if (!activeTurn || !existing) {
        return state;
      }
      const { index, part } = existing;
      const request = part.request;
      const answers = { ...request.answers ?? {} };
      if (action.answer === void 0) {
        delete answers[action.questionId];
      } else {
        answers[action.questionId] = action.answer;
      }
      const responseParts = [...activeTurn.responseParts];
      responseParts[index] = {
        ...part,
        request: {
          ...request,
          answers: Object.keys(answers).length > 0 ? answers : void 0
        }
      };
      return {
        ...state,
        activeTurn: {
          ...activeTurn,
          responseParts
        }
      };
    }
    case ActionType.ChatInputCompleted: {
      const activeTurn = state.activeTurn;
      const existing = activeTurn ? findOpenInputRequestPart(activeTurn.responseParts, action.requestId) : void 0;
      if (!activeTurn || !existing) {
        return state;
      }
      const { index, part } = existing;
      const finalAnswers = { ...part.request.answers ?? {}, ...action.answers ?? {} };
      const responseParts = [...activeTurn.responseParts];
      responseParts[index] = {
        ...part,
        request: {
          ...part.request,
          answers: Object.keys(finalAnswers).length > 0 ? finalAnswers : void 0
        },
        response: action.response
      };
      const next = {
        ...state,
        activeTurn: {
          ...activeTurn,
          responseParts
        }
      };
      return {
        ...next,
        status: summaryStatus(next)
      };
    }
    // ── Pending Messages ──────────────────────────────────────────────────
    case ActionType.ChatPendingMessageSet: {
      const entry = { id: action.id, message: action.message };
      if (action.kind === PendingMessageKind.Steering) {
        return { ...state, steeringMessage: entry };
      }
      const existing = state.queuedMessages ?? [];
      const idx = existing.findIndex((m) => m.id === action.id);
      if (idx >= 0) {
        const updated = [...existing];
        updated[idx] = entry;
        return { ...state, queuedMessages: updated };
      }
      return { ...state, queuedMessages: [...existing, entry] };
    }
    case ActionType.ChatPendingMessageRemoved: {
      if (action.kind === PendingMessageKind.Steering) {
        if (!state.steeringMessage || state.steeringMessage.id !== action.id) {
          return state;
        }
        return { ...state, steeringMessage: void 0 };
      }
      const existing = state.queuedMessages;
      if (!existing) {
        return state;
      }
      const filtered = existing.filter((m) => m.id !== action.id);
      return filtered.length === existing.length ? state : { ...state, queuedMessages: filtered.length > 0 ? filtered : void 0 };
    }
    case ActionType.ChatQueuedMessagesReordered: {
      const existing = state.queuedMessages;
      if (!existing) {
        return state;
      }
      const byId = new Map(existing.map((m) => [m.id, m]));
      const ordered = /* @__PURE__ */ new Set();
      const reordered = action.order.filter((id) => {
        if (byId.has(id) && !ordered.has(id)) {
          ordered.add(id);
          return true;
        }
        return false;
      }).map((id) => byId.get(id));
      for (const m of existing) {
        if (!ordered.has(m.id)) {
          reordered.push(m);
        }
      }
      return { ...state, queuedMessages: reordered };
    }
    // ── Draft ─────────────────────────────────────────────────────────────
    case ActionType.ChatDraftChanged:
      return { ...state, draft: action.draft };
    default:
      softAssertNever(action, log);
      return state;
  }
}

// node_modules/@microsoft/agent-host-protocol/dist/types/channels-resource-watch/reducer.js
function resourceWatchReducer(state, action, log) {
  if (action.type === ActionType.ResourceWatchChanged) {
    return state;
  }
  (log ?? console.warn)(`Unhandled action type: ${JSON.stringify(action)}`);
  return state;
}

// node_modules/ws/wrapper.mjs
var import_stream = __toESM(require_stream(), 1);
var import_extension = __toESM(require_extension(), 1);
var import_permessage_deflate = __toESM(require_permessage_deflate(), 1);
var import_receiver = __toESM(require_receiver(), 1);
var import_sender = __toESM(require_sender(), 1);
var import_subprotocol = __toESM(require_subprotocol(), 1);
var import_websocket = __toESM(require_websocket(), 1);
var import_websocket_server = __toESM(require_websocket_server(), 1);
var wrapper_default = import_websocket.default;

// bridge.js
import { createHash } from "node:crypto";
import { createInterface } from "node:readline";
import { readFileSync } from "node:fs";
var ROOT = "ahp-root://";
var config;
var client;
var socket;
var selected;
var chatURI;
var sequence = 0;
var online = false;
var closing = false;
var connecting;
var generation = 0;
var initialized;
var gate = [];
var ready = false;
var messageWatch;
var states = /* @__PURE__ */ new Map();
var cuts = /* @__PURE__ */ new Map();
var waiting = /* @__PURE__ */ new Map();
var offered = /* @__PURE__ */ new Set();
function output(packet) {
  const line = JSON.stringify(packet) + "\n";
  if (Buffer.byteLength(line) > 32 * 1024 * 1024 || process.stdout.writableLength > 16 * 1024 * 1024) {
    process.stderr.write("Protocol presentation capacity exceeded; no commands replayed\n");
    process.exit(2);
  }
  process.stdout.write(line);
}
function publish(uri, action) {
  const state = states.get(uri);
  if (!state) return;
  if (uri === messageWatch?.channel && action?.type === "resourceWatch/changed") {
    void readMessageWatch(messageWatch);
    return;
  }
  if (uri === ROOT) {
    output({ event: "root", state });
    return;
  }
  if (uri.startsWith("ahp-session:")) {
    output({ event: "session", uri, state });
    return;
  }
  if (uri.startsWith("ahp-chat:")) {
    if (uri === chatURI && selected) for (const part of state.activeTurn?.responseParts ?? []) {
      const tool = part.toolCall, key = selected + "/" + tool?.toolCallId;
      if (tool?.status === "running" && tool.contributor?.kind === "client" && tool.contributor.clientId === config.clientId && !offered.has(key)) {
        if (offered.size >= 1024) {
          socket.close(1013, "Client tool capacity exceeded");
          return;
        }
        offered.add(key);
        output({ event: "clientTool", session: selected, chat: uri, turnId: state.activeTurn.id, tool });
      }
    }
    const turnId = action?.turnId;
    const turn = turnId ? state.activeTurn?.id === turnId ? state.activeTurn : state.turns.find((t) => t.id === turnId) : void 0;
    const full = !action || action.type === "chat/turnsLoaded";
    const append = (action?.type === "chat/delta" || action?.type === "chat/reasoning") && turn?.responseParts.some((p) => p.id === action.partId && ["markdown", "reasoning"].includes(p.kind));
    output({
      event: "chat",
      uri,
      sequence,
      title: state.title,
      status: state.status,
      activeTurnId: state.activeTurn?.id,
      turnsNextCursor: state.turnsNextCursor,
      queuedMessages: state.queuedMessages ?? [],
      steeringMessage: state.steeringMessage,
      ...full ? { turns: state.turns, activeTurn: state.activeTurn } : append ? { append: { turnId, partId: action.partId, content: action.content } } : { turn },
      error: state.error
    });
  }
}
function baseline(snapshot) {
  states.set(snapshot.resource, snapshot.state);
  cuts.set(snapshot.resource, snapshot.fromSeq);
  sequence = Math.max(sequence, snapshot.fromSeq);
  publish(snapshot.resource);
}
function apply(envelope) {
  const { channel, action, origin, rejectionReason, serverSeq } = envelope;
  if (serverSeq <= (cuts.get(channel) ?? -1)) return;
  cuts.set(channel, serverSeq);
  sequence = Math.max(sequence, serverSeq);
  if (origin?.clientId === config.clientId) {
    const pending = waiting.get(origin.clientSeq);
    if (pending) {
      waiting.delete(origin.clientSeq);
      clearTimeout(pending.timer);
      rejectionReason ? pending.reject(Object.assign(new Error(rejectionReason), { rejected: true })) : pending.resolve({ accepted: true });
    }
  }
  if (rejectionReason) return;
  const state = states.get(channel);
  if (!state) return;
  const reducer = channel === ROOT ? rootReducer : channel.startsWith("ahp-chat:") ? chatReducer : channel.startsWith("ahp-resource-watch:") ? resourceWatchReducer : sessionReducer;
  states.set(channel, reducer(state, action));
  publish(channel, action);
}
async function connect(recover = false) {
  if (connecting) return connecting;
  connecting = (async () => {
    ready = false;
    gate = [];
    const current = ++generation;
    socket = new wrapper_default(config.url, { headers: config.token ? { Authorization: `Bearer ${config.token}` } : {}, ca: config.caFile ? readFileSync(config.caFile) : void 0, maxPayload: 32 * 1024 * 1024, followRedirects: false });
    await new Promise((resolve, reject) => {
      socket.once("open", resolve);
      socket.once("error", () => reject(new Error("Cannot connect to AHP host")));
    });
    client = new AhpClient(WebSocketTransport.fromSocket(socket), { requestTimeoutMs: 15e3, subscriptionBuffer: 512 });
    const events = client.events();
    client.connect();
    void (async () => {
      try {
        for await (const item of events) {
          if (current !== generation) return;
          if (!ready) {
            if (gate.length >= 512) throw new Error("Handshake capacity exceeded");
            gate.push(item);
          } else consume(item);
        }
      } catch {
        socket.close();
      }
    })();
    const resources = [...states.keys()];
    if (recover && resources.length) {
      const result = await client.reconnect({ clientId: config.clientId, lastSeenServerSeq: sequence, subscriptions: resources });
      if (result.type === "snapshot") {
        for (const snapshot of result.snapshots) baseline(snapshot);
      } else {
        for (const envelope of result.actions) apply(envelope);
        for (const missing of result.missing ?? []) {
          states.delete(missing);
          output({ event: "missing", uri: missing });
        }
      }
    } else {
      initialized = await client.initialize({ clientId: config.clientId, protocolVersions: ["0.9.0"], initialSubscriptions: [ROOT] });
      for (const snapshot of initialized.snapshots ?? []) baseline(snapshot);
      sequence = initialized.serverSeq;
    }
    ready = true;
    for (const item of gate) consume(item);
    gate = [];
    online = true;
    output({ event: "connection", online: true, generation, initialized });
    output({ event: "catalogInvalidated" });
    if (selected) {
      await optionalTools();
      await optionalMessageWatch();
      publish(chatURI);
    }
    void (async () => {
      for await (const state of client.stateChanges()) {
        if (state.status === "closed" && current === generation && !closing) {
          online = false;
          output({ event: "connection", online: false, generation });
          for (const pending of waiting.values()) {
            clearTimeout(pending.timer);
            pending.reject(new Error("Disconnected; command outcome unknown"));
          }
          waiting.clear();
          setTimeout(() => retry(), 250);
        }
      }
    })();
    return initialized;
  })();
  try {
    return await connecting;
  } finally {
    connecting = void 0;
  }
}
function consume(item) {
  if (item.event.type === "action") apply(item.event.params);
  else if (item.channel === ROOT) output({ event: "catalogInvalidated" });
}
var retryDelay = 250;
async function retry() {
  if (closing) return;
  try {
    await connect(true);
    retryDelay = 250;
  } catch {
    output({ event: "connection", online: false, generation });
    retryDelay = Math.min(retryDelay * 2, 5e3);
    setTimeout(() => retry(), retryDelay);
  }
}
async function subscribe(uri, view) {
  const result = await client.subscribe(uri, { view, delivery: { maxBatchDelayMs: 30 } });
  if (!result.result.snapshot) throw new Error("Host omitted required snapshot");
  baseline(result.result.snapshot);
}
async function dispatch(channel, action) {
  if (!online) throw new Error("Offline; nothing automatically retried");
  const handle = client.dispatch(channel, action);
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      waiting.delete(handle.clientSeq);
      reject(new Error("Action echo unavailable; outcome unknown"));
    }, 15e3);
    waiting.set(handle.clientSeq, { resolve, reject, timer });
  });
}
async function optionalTools() {
  try {
    await registerTools();
  } catch {
    output({ event: "optionalUnavailable", capability: "client-tools", message: "Terminal agent UI registration unavailable; core conversation retained" });
  }
}
function messageURI(scope) {
  const topic = initialized?._meta?.["amplifier.dev/capabilities"]?.topics?.["message-metadata"];
  if (topic?.version !== 1 || !topic.uri) return;
  const uri = new URL(topic.uri);
  uri.searchParams.set("scope", scope);
  return { uri: uri.href, watch: topic.watch === true };
}
async function messageRecord(scope, uri) {
  const result = await client.request("resourceRead", { channel: ROOT, uri, encoding: "utf-8" });
  if (result.encoding !== "utf-8" || result.contentType !== "application/json") throw new Error("Invalid message representation");
  const record = JSON.parse(result.data);
  if (record.topic !== "message-metadata" || record.scope !== scope || !Number.isSafeInteger(record.revision) || record.revision < 0 || !record.data || typeof record.data !== "object") throw new Error("Message response changed scope");
  return record;
}
async function stopMessageWatch() {
  const prior = messageWatch;
  messageWatch = void 0;
  if (prior) {
    states.delete(prior.channel);
    cuts.delete(prior.channel);
    await client.unsubscribe(prior.channel);
  }
}
async function readMessageWatch(watch) {
  if (watch !== messageWatch || watch.scope !== selected) return;
  watch.dirty = true;
  if (watch.pending) return watch.pending;
  const connection = client;
  watch.pending = (async () => {
    try {
      do {
        watch.dirty = false;
        const record = await messageRecord(watch.scope, watch.uri);
        if (watch !== messageWatch || watch.scope !== selected || client !== connection) return;
        if (record.revision > (watch.revision ?? -1)) {
          watch.revision = record.revision;
          output({ event: "messageMetadata", generation, scope: watch.scope, record });
        }
      } while (watch.dirty);
    } catch {
      if (watch === messageWatch) output({ event: "optionalUnavailable", capability: "message-watch", message: "Shared reaction updates unavailable; reopen Inspect for current counts. Original receipts retained." });
    } finally {
      watch.pending = void 0;
    }
  })();
  return watch.pending;
}
async function optionalMessageWatch() {
  try {
    await stopMessageWatch();
    const topic = selected && messageURI(selected);
    if (!topic?.watch) return;
    const scope = selected, connection = client, result = await client.createResourceWatch({ uri: topic.uri, recursive: false });
    if (scope !== selected || connection !== client) {
      await connection.unsubscribe(result.channel);
      return;
    }
    messageWatch = { scope, uri: topic.uri, channel: result.channel };
    await subscribe(result.channel);
    await readMessageWatch(messageWatch);
  } catch {
    output({ event: "optionalUnavailable", capability: "message-watch", message: "Shared reaction updates unavailable; reopen Inspect for current counts. Original receipts retained." });
  }
}
async function registerTools() {
  const suffix = createHash("sha256").update(config.clientId).digest("hex").slice(0, 16);
  await dispatch(selected, { type: "session/activeClientSet", activeClient: { clientId: config.clientId, displayName: "Amplifier Unified TUI", tools: [
    { name: `amplifier_tui_inspect_${suffix}`, title: "Inspect this terminal view", description: "Read current renderer revision and selected view; private draft only when includeDraft=true.", inputSchema: { type: "object", properties: { includeDraft: { type: "boolean" } } } },
    { name: `amplifier_tui_action_${suffix}`, title: "Control this terminal view", description: "Use the current renderer revision for private drafts, navigation, quotes or negotiated message metadata. Queue and steering actions explicitly admit selected-chat user text. Offered settings, naming and their original receipts use the same human actions without sending drafts; unknown changes are never replayed.", inputSchema: { type: "object", required: ["action", "expectedRevision"], properties: { action: { type: "string", enum: ["draft.replace", "view.select", "panel.open", "message.reply", "message.replyClear", "message.read", "message.reaction", "message.receipt", "message.refresh", "message.submissionInspect", "queue", "queue_edit", "queue_remove", "queue_run", "queue_inspect", "steer", "steer_remove", "steer_inspect", "settings", "setting_choices", "setting_set", "rename", "host_effects", "host_receipt"] }, expectedRevision: { type: "integer" }, args: { type: "object" } } } }
  ] } });
}
async function command(method, p) {
  if (method === "open") {
    config = p;
    return connect();
  }
  if (method === "close") {
    closing = true;
    await client?.shutdown();
    return {};
  }
  if (!online) throw new Error("AHP host disconnected");
  if (method === "list") return client.request("listSessions", { channel: ROOT, limit: 50, ...p.cursor ? { cursor: p.cursor } : {} });
  if (method === "select") {
    if (selected === p.session && states.has(chatURI)) {
      publish(selected);
      publish(chatURI);
      return { session: selected, chat: chatURI };
    }
    const prior = selected, priorChat = chatURI;
    await subscribe(p.session);
    const nextChat = states.get(p.session).defaultChat;
    if (!nextChat) throw new Error("Session has no default chat");
    try {
      await subscribe(nextChat, { turns: 50 });
    } catch (error) {
      await client.unsubscribe(p.session);
      states.delete(p.session);
      throw error;
    }
    selected = p.session;
    chatURI = nextChat;
    for (const uri of [prior, priorChat]) if (uri && uri !== selected && uri !== chatURI) {
      await client.unsubscribe(uri);
      states.delete(uri);
      cuts.delete(uri);
    }
    await optionalTools();
    await optionalMessageWatch();
    publish(chatURI);
    return { session: selected, chat: chatURI };
  }
  if (method === "detach") {
    await stopMessageWatch();
    for (const uri of [selected, chatURI]) if (uri) {
      await client.unsubscribe(uri);
      states.delete(uri);
      cuts.delete(uri);
    }
    selected = chatURI = void 0;
    return {};
  }
  if (method === "capability") {
    const manifest = initialized?._meta?.["amplifier.dev/capabilities"];
    const action = manifest?.version === 1 ? manifest.actions?.[p.action] : void 0;
    if (!action || action.method !== "x-amplifier/capabilityAction" || manifest.topics?.[action.topic]?.version !== 1) throw Object.assign(new Error("Capability action unavailable"), { rejected: true });
    return client.request(action.method, { channel: p.channel ?? ROOT, topic: action.topic, operation: action.operation, version: 1, args: p.args ?? {}, commandId: p.commandId });
  }
  if (method === "messageDescriptor") {
    if (p.session !== selected) throw Object.assign(new Error("Selection changed"), { rejected: true });
    const topic = messageURI(p.session);
    if (!topic) throw Object.assign(new Error("Message metadata unavailable"), { rejected: true });
    return (await messageRecord(p.session, topic.uri)).data;
  }
  if (method === "managed") {
    const cap = initialized?._meta?.["amplifier.dev/managedCreation"];
    if (cap?.version !== 1 || cap.method !== "x-amplifier/managedSession" || !cap.operations?.includes(p.operation)) throw Object.assign(new Error("Managed creation capability unavailable"), { rejected: true });
    return client.request(cap.method, { channel: ROOT, operation: p.operation, args: p.args });
  }
  if (method === "lifecycle") {
    const cap = initialized?._meta?.["amplifier.dev/sessionLifecycle"];
    if (cap?.version !== 1 || cap.method !== "x-amplifier/sessionLifecycle" || cap.deletion !== "preserve-history") throw Object.assign(new Error("Preserve-history lifecycle capability unavailable"), { rejected: true });
    return client.request(cap.method, { channel: p.session, operation: p.operation, args: p.args ?? {} });
  }
  if (method === "create") {
    const provider = p.provider ?? states.get(ROOT)?.agents?.[0]?.provider;
    if (!provider) throw new Error("Host advertised no agent");
    await client.request("createSession", { channel: p.session, provider, workingDirectories: [p.cwd ?? initialized.defaultDirectory] });
    return { session: p.session };
  }
  if (method === "toolComplete") return dispatch(p.chat, { type: "chat/toolCallComplete", turnId: p.turnId, toolCallId: p.toolCallId, result: p.result });
  if (method === "send") return dispatch(p.chat, { type: "chat/turnStarted", turnId: p.commandId, startedAt: (/* @__PURE__ */ new Date()).toISOString(), message: { text: p.text, origin: { kind: "user" }, ...p.reply ? { _meta: { "amplifier.dev/messageReply": p.reply } } : {} } });
  if (method === "queue" || method === "steer") {
    if (initialized?._meta?.["amplifier.dev/host"]?.features?.[method] !== true || p.chat !== chatURI) throw Object.assign(new Error("Selected host queue unavailable"), { rejected: true });
    if (!["set", "remove"].includes(p.operation) || typeof p.pendingId !== "string" || !p.pendingId || p.pendingId.length > 128 || p.operation === "set" && (typeof p.text !== "string" || !p.text.trim())) throw Object.assign(new Error("Bounded pending user intent required"), { rejected: true });
    const action = p.operation === "remove" ? { type: "chat/pendingMessageRemoved", kind: method === "steer" ? "steering" : "queued", id: p.pendingId } : { type: "chat/pendingMessageSet", kind: method === "steer" ? "steering" : "queued", id: p.pendingId, message: { text: p.text, origin: { kind: "user" } } };
    return dispatch(p.chat, action);
  }
  if (method === "cancel") return dispatch(p.chat, { type: "chat/turnCancelled", turnId: p.turnId, duration: 0 });
  if (method === "refreshSession") {
    if (p.session !== selected) throw Object.assign(new Error("Selection changed"), { rejected: true });
    const result = await client.request("subscribe", { channel: p.session });
    if (!result.snapshot) throw new Error("Host omitted selected snapshot");
    baseline(result.snapshot);
    return {};
  }
  if (method === "refreshChat") {
    if (p.session !== selected) throw Object.assign(new Error("Selection changed"), { rejected: true });
    const result = await client.request("subscribe", { channel: chatURI, view: { turns: 50 } });
    if (!result.snapshot) throw new Error("Host omitted selected chat snapshot");
    baseline(result.snapshot);
    return {};
  }
  if (method === "configure") return dispatch(p.session, { type: "session/configChanged", config: p.config });
  if (method === "rename") return dispatch(p.session, { type: "session/titleChanged", title: p.title });
  if (method === "decision") return dispatch(p.chat, { type: "chat/toolCallConfirmed", turnId: p.turnId, toolCallId: p.toolCallId, approved: p.approved, confirmed: "user-action", selectedOptionId: p.option });
  if (method === "history") return client.request("fetchTurns", { channel: p.chat, cursor: p.cursor });
  if (method === "receipt") {
    if (!initialized?._meta?.["amplifier.dev/host"]?.receipts) throw new Error("Host has not advertised durable receipt lookup");
    return client.request("x-commandReceipt", { channel: p.chat, commandId: p.commandId });
  }
  if (method === "disconnect") {
    socket.close();
    return {};
  }
  throw new Error("Unsupported protocol operation");
}
var input = createInterface({ input: process.stdin, crlfDelay: Infinity });
var inFlight = 0;
input.on("line", (line) => {
  if (Buffer.byteLength(line) > 2 * 1024 * 1024 || ++inFlight > 32) {
    process.exit(2);
    return;
  }
  let packet;
  try {
    packet = JSON.parse(line);
  } catch {
    process.exit(2);
    return;
  }
  void command(packet.method, packet.params ?? {}).then((result) => output({ id: packet.id, result })).catch((error) => output({ id: packet.id, error: { message: error.message, rejected: !!error.rejected } })).finally(() => {
    inFlight--;
    if (packet.method === "close") process.exit(0);
  });
});
input.on("close", () => {
  closing = true;
  void client?.shutdown().finally(() => process.exit(0));
});
