import 'package:intl/intl.dart';
import 'package:timeago/timeago.dart' as timeago;

/// Centralized date formatting utility for consistent date display.
///
/// Implements POLISH-01 requirement:
/// - Relative dates shown for items <7 days old ("2h ago", "3 days ago")
/// - Absolute dates shown for items >=7 days old ("Jan 18, 2026")
class DateFormatter {
  /// Initialize timeago locales.
  ///
  /// Call early in app lifecycle (in main.dart after WidgetsFlutterBinding.ensureInitialized()).
  /// Default English locale messages are already loaded; add more if needed.
  static void init() {
    // Default locale messages already loaded by timeago package
    // Add additional locales here if needed:
    // timeago.setLocaleMessages('fr', timeago.FrMessages());
  }

  /// Format date for display: relative for <7 days, absolute for older.
  ///
  /// Examples:
  /// - 2 hours ago -> "about 2 hours ago"
  /// - 3 days ago -> "3 days ago"
  /// - 10 days ago -> "Jan 18, 2026"
  static String format(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays < 7) {
      // Use timeago for relative: "2h ago", "4d ago", "Yesterday"
      return timeago.format(date);
    } else {
      // Use intl for absolute: "Jan 18, 2026"
      return DateFormat.yMMMd().format(date);
    }
  }

  /// Format time only for display: "5:08 PM"
  ///
  /// Useful for message timestamps within the same day.
  static String formatTime(DateTime date) {
    return DateFormat.jm().format(date);
  }

  /// Format date and time: "Jan 18, 2026 5:08 PM"
  ///
  /// Useful for detailed timestamps.
  static String formatDateTime(DateTime date) {
    return '${DateFormat.yMMMd().format(date)} ${DateFormat.jm().format(date)}';
  }
}
