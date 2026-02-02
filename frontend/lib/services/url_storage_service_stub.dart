/// Stub implementation for non-web platforms.
///
/// This stub is used during Flutter tests and on native platforms
/// where dart:html is not available. All methods are no-ops or return null.
class UrlStorageService {
  /// No-op on non-web platforms - sessionStorage not available.
  void storeReturnUrl(String url) {
    // No-op on non-web platforms
  }

  /// Returns null on non-web platforms - sessionStorage not available.
  String? getReturnUrl() => null;

  /// No-op on non-web platforms - sessionStorage not available.
  void clearReturnUrl() {
    // No-op on non-web platforms
  }
}
