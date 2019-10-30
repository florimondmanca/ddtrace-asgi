# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.2.0 - 2019-10-30

### Changed

- The `tracer`, `service` and `distributed_tracing` for `TraceMiddleware` are now keyword-only. (Pull #9)

### Added

- The `tracer` for `TraceMiddleware` is now the global `ddtrace.tracer` by default. (Pull #9)

## 0.1.0 - 2019-10-23

Initial release.

### Added

- Add `TracingMiddleware`.
