// Debug override for Immich v2.5.6 API worker.
// Mounted into the container to identify where startup stalls before binding :2283.
"use strict";

const { NestFactory } = require("@nestjs/core");
const { configureTelemetry, configureExpress } = require("../app.common");
const { ApiModule } = require("../app.module");
const { AppRepository } = require("../repositories/app.repository");
const { ApiService } = require("../services/api.service");
const { isStartUpError } = require("../utils/misc");

function mark(msg) {
  // stderr so it stands out in docker logs
  console.error(`[debug-api] ${msg}`);
}

async function bootstrap() {
  process.title = "immich-api";
  configureTelemetry();

  mark("NestFactory.create(ApiModule) start");
  const app = await NestFactory.create(ApiModule, { bufferLogs: true });
  mark("NestFactory.create(ApiModule) done");

  app.get(AppRepository).setCloseFn(() => app.close());

  const watchdog = setInterval(() => {
    mark("still starting (no listen yet)");
  }, 30000);
  watchdog.unref?.();

  try {
    mark("configureExpress start");
    await configureExpress(app, { ssr: ApiService });
    mark("configureExpress done (should be listening now)");
  } finally {
    clearInterval(watchdog);
  }
}

bootstrap().catch((error) => {
  // Mirror upstream behavior but be noisy.
  if (!isStartUpError(error)) {
    console.error("[debug-api] bootstrap error:", error);
  } else {
    console.error("[debug-api] startup error:", error?.message || String(error));
  }
  process.exit(1);
});

