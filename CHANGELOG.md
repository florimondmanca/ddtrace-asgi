# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.2.1 - 2019-10-31

### Fixed

- Improve resilience to ASGI protocol violations. (Pull #11)

## 0.2.0 - 2019-10-30

### Changed

- The `tracer`, `service` and `distributed_tracing` parameters of `TraceMiddleware` are now keyword-only. (Pull #10)

### Added

- The `tracer` for `TraceMiddleware` is now the global `ddtrace.tracer` by default. (Pull #10)

## 0.1.0 - 2019-10-23

Initial release.

### Added

- Add `TracingMiddleware`.
