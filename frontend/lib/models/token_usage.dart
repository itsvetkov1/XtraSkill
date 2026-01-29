/// Token usage data model for monthly budget tracking.
library;

/// Monthly token usage statistics from /auth/usage endpoint
class TokenUsage {
  final double totalCost;
  final int totalRequests;
  final int totalInputTokens;
  final int totalOutputTokens;
  final String monthStart;
  final double budget;

  TokenUsage({
    required this.totalCost,
    required this.totalRequests,
    required this.totalInputTokens,
    required this.totalOutputTokens,
    required this.monthStart,
    required this.budget,
  });

  factory TokenUsage.fromJson(Map<String, dynamic> json) {
    return TokenUsage(
      totalCost: (json['total_cost'] as num).toDouble(),
      totalRequests: json['total_requests'] as int,
      totalInputTokens: json['total_input_tokens'] as int,
      totalOutputTokens: json['total_output_tokens'] as int,
      monthStart: json['month_start'] as String,
      budget: (json['budget'] as num).toDouble(),
    );
  }

  /// Total tokens used (input + output)
  int get totalTokens => totalInputTokens + totalOutputTokens;

  /// Cost as percentage of budget (0.0 to 1.0, clamped)
  double get costPercentage => (totalCost / budget).clamp(0.0, 1.0);

  /// Cost percentage as display string (e.g., "12.5%")
  String get costPercentageDisplay =>
      '${(costPercentage * 100).toStringAsFixed(1)}%';
}
