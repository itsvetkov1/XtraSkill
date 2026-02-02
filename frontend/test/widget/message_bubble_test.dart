/// Widget tests for MessageBubble component.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/message.dart';
import 'package:frontend/screens/conversation/widgets/message_bubble.dart';

void main() {
  group('MessageBubble Widget Tests', () {
    Widget buildTestWidget(Message message) {
      return MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: MessageBubble(message: message),
          ),
        ),
      );
    }

    group('User Messages', () {
      late Message userMessage;

      setUp(() {
        userMessage = Message(
          id: 'test-1',
          role: MessageRole.user,
          content: 'Hello, this is a test message',
          createdAt: DateTime.now(),
        );
      });

      testWidgets('aligned to center right', (tester) async {
        await tester.pumpWidget(buildTestWidget(userMessage));

        final align = tester.widget<Align>(find.byType(Align).first);
        expect(align.alignment, Alignment.centerRight);
      });

      testWidgets('does not show copy button', (tester) async {
        await tester.pumpWidget(buildTestWidget(userMessage));

        expect(find.byIcon(Icons.copy), findsNothing);
      });

      testWidgets('displays message content', (tester) async {
        await tester.pumpWidget(buildTestWidget(userMessage));

        expect(find.text('Hello, this is a test message'), findsOneWidget);
      });

      testWidgets('uses primary color background', (tester) async {
        await tester.pumpWidget(buildTestWidget(userMessage));

        final container = tester.widget<Container>(find.byType(Container).first);
        final decoration = container.decoration as BoxDecoration?;
        expect(decoration, isNotNull);
        // Verify it has a color (primary color from theme)
        expect(decoration!.color, isNotNull);
      });
    });

    group('Assistant Messages', () {
      late Message assistantMessage;

      setUp(() {
        assistantMessage = Message(
          id: 'test-2',
          role: MessageRole.assistant,
          content: 'This is an assistant response',
          createdAt: DateTime.now(),
        );
      });

      testWidgets('aligned to center left', (tester) async {
        await tester.pumpWidget(buildTestWidget(assistantMessage));

        final align = tester.widget<Align>(find.byType(Align).first);
        expect(align.alignment, Alignment.centerLeft);
      });

      testWidgets('shows copy button', (tester) async {
        await tester.pumpWidget(buildTestWidget(assistantMessage));

        expect(find.byIcon(Icons.copy), findsOneWidget);
      });

      testWidgets('copy button has tooltip', (tester) async {
        await tester.pumpWidget(buildTestWidget(assistantMessage));

        final iconButton = tester.widget<IconButton>(find.byType(IconButton));
        expect(iconButton.tooltip, 'Copy to clipboard');
      });

      testWidgets('displays message content', (tester) async {
        await tester.pumpWidget(buildTestWidget(assistantMessage));

        expect(find.text('This is an assistant response'), findsOneWidget);
      });
    });

    group('Text Content', () {
      testWidgets('uses SelectableText for content', (tester) async {
        final message = Message(
          id: 'test-3',
          role: MessageRole.user,
          content: 'Selectable text',
          createdAt: DateTime.now(),
        );

        await tester.pumpWidget(buildTestWidget(message));

        expect(find.byType(SelectableText), findsOneWidget);
      });

      testWidgets('long content is displayed correctly', (tester) async {
        final longContent = 'This is a very long message. ' * 20;
        final message = Message(
          id: 'test-4',
          role: MessageRole.assistant,
          content: longContent,
          createdAt: DateTime.now(),
        );

        await tester.pumpWidget(buildTestWidget(message));

        expect(find.textContaining('This is a very long message.'), findsOneWidget);
      });
    });
  });
}
