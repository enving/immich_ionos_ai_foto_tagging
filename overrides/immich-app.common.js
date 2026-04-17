// Debug override for Immich v2.5.6 `dist/app.common.js`.
// Adds progress markers to determine which await in `configureExpress()` blocks.
"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
  return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.configureTelemetry = configureTelemetry;
exports.configureExpress = configureExpress;
const body_parser_1 = require("body-parser");
const compression_1 = __importDefault(require("compression"));
const cookie_parser_1 = __importDefault(require("cookie-parser"));
const node_fs_1 = require("node:fs");
const sirv_1 = __importDefault(require("sirv"));
const constants_1 = require("./constants");
const websocket_adapter_1 = require("./middleware/websocket.adapter");
const config_repository_1 = require("./repositories/config.repository");
const logging_repository_1 = require("./repositories/logging.repository");
const telemetry_repository_1 = require("./repositories/telemetry.repository");
const misc_1 = require("./utils/misc");

function dbg(msg) {
  console.error(`[debug-express] ${msg}`);
}

function configureTelemetry() {
  const { telemetry } = new config_repository_1.ConfigRepository().getEnv();
  if (telemetry.metrics.size > 0) {
    (0, telemetry_repository_1.bootstrapTelemetry)(telemetry.apiPort);
  }
}

async function configureExpress(app, { permitSwaggerWrite = true, ssr, }) {
  const configRepository = app.get(config_repository_1.ConfigRepository);
  const { environment, host, port, resourcePaths, network } = configRepository.getEnv();

  dbg(`before app.resolve(LoggingRepository) host=${host || ""} port=${port}`);
  const logger = await app.resolve(logging_repository_1.LoggingRepository);
  dbg("after app.resolve(LoggingRepository)");

  logger.setContext("Bootstrap");
  app.useLogger(logger);
  app.set("trust proxy", ["loopback", ...network.trustedProxies]);
  app.set("etag", "strong");
  app.use((0, cookie_parser_1.default)());
  app.use((0, body_parser_1.json)({ limit: "10mb" }));
  if (configRepository.isDev()) {
    app.enableCors();
  }
  app.setGlobalPrefix("api", { exclude: constants_1.excludePaths });
  app.useWebSocketAdapter(new websocket_adapter_1.WebSocketAdapter(app));
  (0, misc_1.useSwagger)(app, { write: configRepository.isDev() && permitSwaggerWrite });
  if ((0, node_fs_1.existsSync)(resourcePaths.web.root)) {
    app.use((0, sirv_1.default)(resourcePaths.web.root, {
      etag: true,
      gzip: true,
      brotli: true,
      extensions: [],
      setHeaders: (res, pathname) => {
        if (pathname.startsWith(`/_app/immutable`) && res.statusCode === 200) {
          res.setHeader("cache-control", "public,max-age=31536000,immutable");
        }
      },
    }));
  }
  app.use(app.get(ssr).ssr(constants_1.excludePaths));
  app.use((0, compression_1.default)());

  dbg("before app.listen()");
  const server = await (host ? app.listen(port, host) : app.listen(port));
  dbg("after app.listen()");

  server.requestTimeout = 24 * 60 * 60 * 1000;
  dbg("before app.getUrl()");
  logger.log(`Immich Server is listening on ${await app.getUrl()} [v${constants_1.serverVersion}] [${environment}] `);
  dbg("after app.getUrl()");
}

