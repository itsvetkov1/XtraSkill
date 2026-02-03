/// Budget warning banner widget for threshold notifications.
library;

import 'package:flutter/material.dart';

import '../../../providers/budget_provider.dart';

/// Banner displaying budget warning messages based on threshold status
///
/// Shows appropriate message and styling for each BudgetStatus:
/// - normal: Returns nothing (SizedBox.shrink)
/// - warning (80%): Yellow/orange banner with dismiss action
/// - urgent (95%): Orange/red banner with dismiss action
/// - exhausted (100%): Red banner, no dismiss (stays visible)
///
/// Per BUD-05: Shows percentage only, no monetary amounts.
class BudgetWarningBanner extends StatefulWidget {
  /// Current budget status
  final BudgetStatus status;

  /// Current usage percentage (0-100)
  final int percentage;

  const BudgetWarningBanner({
    super.key,
    required this.status,
    required this.percentage,
  });

  @override
  State<BudgetWarningBanner> createState() => _BudgetWarningBannerState();
}

class _BudgetWarningBannerState extends State<BudgetWarningBanner> {
  bool _dismissed = false;

  @override
  void didUpdateWidget(BudgetWarningBanner oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Reset dismissed state when status changes to a higher severity
    if (widget.status != oldWidget.status) {
      _dismissed = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Don't show anything for normal status
    if (widget.status == BudgetStatus.normal) {
      return const SizedBox.shrink();
    }

    // Don't show if dismissed (except exhausted which cannot be dismissed)
    if (_dismissed && widget.status != BudgetStatus.exhausted) {
      return const SizedBox.shrink();
    }

    final colorScheme = Theme.of(context).colorScheme;

    // Configure banner based on status
    final (backgroundColor, textColor, message, canDismiss) = switch (widget.status) {
      BudgetStatus.warning => (
          colorScheme.tertiaryContainer,
          colorScheme.onTertiaryContainer,
          "You've used ${widget.percentage}% of your token budget",
          true,
        ),
      BudgetStatus.urgent => (
          Colors.orange[100]!,
          Colors.orange[900]!,
          'Almost at limit - limited messages remaining',
          true,
        ),
      BudgetStatus.exhausted => (
          colorScheme.errorContainer,
          colorScheme.onErrorContainer,
          'Budget exhausted - unable to send messages',
          false,
        ),
      BudgetStatus.normal => (
          Colors.transparent,
          Colors.transparent,
          '',
          false,
        ),
    };

    return MaterialBanner(
      content: Text(
        message,
        style: TextStyle(color: textColor),
      ),
      backgroundColor: backgroundColor,
      actions: [
        if (canDismiss)
          TextButton(
            onPressed: () => setState(() => _dismissed = true),
            child: Text(
              'Dismiss',
              style: TextStyle(color: textColor),
            ),
          )
        else
          // Exhausted state shows no dismiss, just acknowledge text
          Text(
            'View history only',
            style: TextStyle(
              color: textColor,
              fontSize: 12,
            ),
          ),
      ],
    );
  }
}
