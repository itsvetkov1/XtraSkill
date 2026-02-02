import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/token_usage.dart';

void main() {
  group('TokenUsage', () {
    group('fromJson', () {
      test('creates instance from complete JSON', () {
        final json = {
          'total_cost': 12.5,
          'total_requests': 100,
          'total_input_tokens': 5000,
          'total_output_tokens': 3000,
          'month_start': '2026-02-01',
          'budget': 100.0,
        };

        final usage = TokenUsage.fromJson(json);

        expect(usage.totalCost, 12.5);
        expect(usage.totalRequests, 100);
        expect(usage.totalInputTokens, 5000);
        expect(usage.totalOutputTokens, 3000);
        expect(usage.monthStart, '2026-02-01');
        expect(usage.budget, 100.0);
      });

      test('handles numeric type coercion for cost', () {
        // API may return int instead of double for whole numbers
        final json = {
          'total_cost': 50, // int instead of double
          'total_requests': 200,
          'total_input_tokens': 10000,
          'total_output_tokens': 8000,
          'month_start': '2026-02-01',
          'budget': 100, // int instead of double
        };

        final usage = TokenUsage.fromJson(json);

        expect(usage.totalCost, 50.0);
        expect(usage.totalCost, isA<double>());
        expect(usage.budget, 100.0);
        expect(usage.budget, isA<double>());
      });

      test('handles decimal cost values', () {
        final json = {
          'total_cost': 0.0023456,
          'total_requests': 5,
          'total_input_tokens': 100,
          'total_output_tokens': 50,
          'month_start': '2026-02-01',
          'budget': 25.0,
        };

        final usage = TokenUsage.fromJson(json);

        expect(usage.totalCost, closeTo(0.0023456, 0.0000001));
      });
    });

    group('totalTokens', () {
      test('returns sum of input and output tokens', () {
        final usage = TokenUsage(
          totalCost: 10.0,
          totalRequests: 50,
          totalInputTokens: 5000,
          totalOutputTokens: 3000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.totalTokens, 8000);
      });

      test('handles zero tokens', () {
        final usage = TokenUsage(
          totalCost: 0.0,
          totalRequests: 0,
          totalInputTokens: 0,
          totalOutputTokens: 0,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.totalTokens, 0);
      });

      test('handles large token counts', () {
        final usage = TokenUsage(
          totalCost: 500.0,
          totalRequests: 1000,
          totalInputTokens: 1000000,
          totalOutputTokens: 500000,
          monthStart: '2026-02-01',
          budget: 1000.0,
        );

        expect(usage.totalTokens, 1500000);
      });
    });

    group('costPercentage', () {
      test('returns correct ratio', () {
        final usage = TokenUsage(
          totalCost: 12.5,
          totalRequests: 100,
          totalInputTokens: 5000,
          totalOutputTokens: 3000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentage, 0.125);
      });

      test('clamps to 0.0 when cost is 0', () {
        final usage = TokenUsage(
          totalCost: 0.0,
          totalRequests: 0,
          totalInputTokens: 0,
          totalOutputTokens: 0,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentage, 0.0);
      });

      test('clamps to 1.0 when over budget', () {
        final usage = TokenUsage(
          totalCost: 150.0,
          totalRequests: 500,
          totalInputTokens: 50000,
          totalOutputTokens: 30000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentage, 1.0);
      });

      test('returns exactly 1.0 at budget limit', () {
        final usage = TokenUsage(
          totalCost: 100.0,
          totalRequests: 300,
          totalInputTokens: 30000,
          totalOutputTokens: 20000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentage, 1.0);
      });

      test('handles small fractional percentage', () {
        final usage = TokenUsage(
          totalCost: 0.05,
          totalRequests: 2,
          totalInputTokens: 100,
          totalOutputTokens: 50,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentage, 0.0005);
      });
    });

    group('costPercentageDisplay', () {
      test('formats as percentage string', () {
        final usage = TokenUsage(
          totalCost: 12.5,
          totalRequests: 100,
          totalInputTokens: 5000,
          totalOutputTokens: 3000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentageDisplay, '12.5%');
      });

      test('shows 100.0% when over budget', () {
        final usage = TokenUsage(
          totalCost: 150.0,
          totalRequests: 500,
          totalInputTokens: 50000,
          totalOutputTokens: 30000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentageDisplay, '100.0%');
      });

      test('handles fractional percentages', () {
        final usage = TokenUsage(
          totalCost: 33.33,
          totalRequests: 150,
          totalInputTokens: 15000,
          totalOutputTokens: 10000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentageDisplay, '33.3%');
      });

      test('shows 0.0% when no usage', () {
        final usage = TokenUsage(
          totalCost: 0.0,
          totalRequests: 0,
          totalInputTokens: 0,
          totalOutputTokens: 0,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentageDisplay, '0.0%');
      });

      test('shows 50.0% at half budget', () {
        final usage = TokenUsage(
          totalCost: 50.0,
          totalRequests: 200,
          totalInputTokens: 20000,
          totalOutputTokens: 15000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.costPercentageDisplay, '50.0%');
      });

      test('handles very small percentages', () {
        final usage = TokenUsage(
          totalCost: 0.01,
          totalRequests: 1,
          totalInputTokens: 10,
          totalOutputTokens: 5,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        // 0.01% of budget
        expect(usage.costPercentageDisplay, '0.0%');
      });
    });

    group('computed properties calculate correctly', () {
      test('all computed properties work together', () {
        final usage = TokenUsage(
          totalCost: 12.5,
          totalRequests: 100,
          totalInputTokens: 5000,
          totalOutputTokens: 3000,
          monthStart: '2026-02-01',
          budget: 100.0,
        );

        expect(usage.totalTokens, 8000);
        expect(usage.costPercentage, 0.125);
        expect(usage.costPercentageDisplay, '12.5%');
      });
    });
  });
}
