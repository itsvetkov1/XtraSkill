# BA Assistant Frontend

Flutter application for the Business Analyst Assistant.

## Getting Started

### Prerequisites

- Flutter SDK ^3.9.2
- Dart SDK (included with Flutter)

### Installation

```bash
# Install dependencies
flutter pub get

# Generate mocks for testing (if needed)
dart run build_runner build
```

### Running the App

```bash
# Run in debug mode
flutter run

# Run in Chrome (web)
flutter run -d chrome

# Run in Windows
flutter run -d windows
```

## Testing

### Running Tests

```bash
# Run all tests
flutter test

# Run tests with coverage
flutter test --coverage

# Run specific test file
flutter test test/unit/chats_provider_test.dart

# Run tests matching a pattern
flutter test --name "should load"
```

### Coverage Reports

Generate HTML coverage reports:

```bash
# Prerequisites: Install lcov
# Ubuntu/Debian: sudo apt install lcov
# macOS: brew install lcov
# Windows: Use WSL or Git Bash with lcov

# Generate report (runs tests first)
./coverage_report.sh

# Generate report from existing lcov.info
./coverage_report.sh --skip-tests

# Open report
# Linux: xdg-open coverage/html/index.html
# macOS: open coverage/html/index.html
# Windows: start coverage/html/index.html
```

### Test Structure

```
test/
  unit/          # Unit tests for providers/services
  widget/        # Widget tests for UI components
```

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)
