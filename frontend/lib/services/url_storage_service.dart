/// Conditional export for UrlStorageService.
///
/// On web platforms (dart.library.html available), exports the web implementation
/// that uses dart:html sessionStorage.
///
/// On non-web platforms and in tests, exports the stub implementation
/// that provides no-op methods.
export 'url_storage_service_stub.dart'
    if (dart.library.html) 'url_storage_service_web.dart';
