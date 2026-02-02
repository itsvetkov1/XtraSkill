/// Widget tests for HomeScreen (FWID-05).
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/project.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/providers/chats_provider.dart';
import 'package:frontend/providers/project_provider.dart';
import 'package:frontend/providers/provider_provider.dart';
import 'package:frontend/screens/home_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'home_screen_test.mocks.dart';

@GenerateNiceMocks([
  MockSpec<AuthProvider>(),
  MockSpec<ProjectProvider>(),
  MockSpec<ChatsProvider>(),
  MockSpec<ProviderProvider>(),
])
void main() {
  group('HomeScreen Widget Tests', () {
    late MockAuthProvider mockAuthProvider;
    late MockProjectProvider mockProjectProvider;
    late MockChatsProvider mockChatsProvider;
    late MockProviderProvider mockProviderProvider;

    setUp(() {
      mockAuthProvider = MockAuthProvider();
      mockProjectProvider = MockProjectProvider();
      mockChatsProvider = MockChatsProvider();
      mockProviderProvider = MockProviderProvider();

      // Default mock behavior
      when(mockAuthProvider.displayName).thenReturn('John');
      when(mockAuthProvider.email).thenReturn('john@example.com');

      when(mockProjectProvider.isLoading).thenReturn(false);
      when(mockProjectProvider.projects).thenReturn([]);
      when(mockProjectProvider.loadProjects()).thenAnswer((_) async {});

      when(mockProviderProvider.selectedProvider).thenReturn('anthropic');
    });

    Widget buildTestWidget() {
      return MaterialApp(
        home: MultiProvider(
          providers: [
            ChangeNotifierProvider<AuthProvider>.value(value: mockAuthProvider),
            ChangeNotifierProvider<ProjectProvider>.value(
                value: mockProjectProvider),
            ChangeNotifierProvider<ChatsProvider>.value(
                value: mockChatsProvider),
            ChangeNotifierProvider<ProviderProvider>.value(
                value: mockProviderProvider),
          ],
          child: const HomeScreen(),
        ),
      );
    }

    group('Greeting', () {
      testWidgets('shows greeting with displayName', (tester) async {
        when(mockAuthProvider.displayName).thenReturn('John');

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Welcome back, John'), findsOneWidget);
      });

      testWidgets('uses email prefix when no displayName', (tester) async {
        when(mockAuthProvider.displayName).thenReturn(null);
        when(mockAuthProvider.email).thenReturn('jane@example.com');

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Welcome back, jane'), findsOneWidget);
      });

      testWidgets('defaults to "there" when no name or email', (tester) async {
        when(mockAuthProvider.displayName).thenReturn(null);
        when(mockAuthProvider.email).thenReturn(null);

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Welcome back, there'), findsOneWidget);
      });

      testWidgets('uses email prefix when displayName is empty', (tester) async {
        when(mockAuthProvider.displayName).thenReturn('');
        when(mockAuthProvider.email).thenReturn('alice@example.com');

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Welcome back, alice'), findsOneWidget);
      });
    });

    group('Action Buttons', () {
      testWidgets('shows New Chat button', (tester) async {
        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('New Chat'), findsOneWidget);
        expect(find.byIcon(Icons.chat_bubble), findsOneWidget);
      });

      testWidgets('shows Browse Projects button', (tester) async {
        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Browse Projects'), findsOneWidget);
        expect(find.byIcon(Icons.folder_outlined), findsOneWidget);
      });
    });

    group('Recent Projects', () {
      testWidgets('shows empty hint when no projects', (tester) async {
        when(mockProjectProvider.projects).thenReturn([]);
        when(mockProjectProvider.isLoading).thenReturn(false);

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(
            find.text('No projects yet - create your first one!'), findsOneWidget);
      });

      testWidgets('shows recent projects section', (tester) async {
        final projects = [
          Project(
            id: '1',
            name: 'Project Alpha',
            description: 'First project',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
          Project(
            id: '2',
            name: 'Project Beta',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
        ];
        when(mockProjectProvider.projects).thenReturn(projects);

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Recent Projects'), findsOneWidget);
        expect(find.text('See all'), findsOneWidget);
        expect(find.text('Project Alpha'), findsOneWidget);
        expect(find.text('Project Beta'), findsOneWidget);
      });

      testWidgets('shows max 3 projects', (tester) async {
        final projects = List.generate(
            5,
            (i) => Project(
                  id: '$i',
                  name: 'Project $i',
                  createdAt: DateTime.now(),
                  updatedAt: DateTime.now(),
                ));
        when(mockProjectProvider.projects).thenReturn(projects);

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Project 0'), findsOneWidget);
        expect(find.text('Project 1'), findsOneWidget);
        expect(find.text('Project 2'), findsOneWidget);
        expect(find.text('Project 3'), findsNothing);
        expect(find.text('Project 4'), findsNothing);
      });

      testWidgets('hides empty hint during loading', (tester) async {
        when(mockProjectProvider.isLoading).thenReturn(true);
        when(mockProjectProvider.projects).thenReturn([]);

        await tester.pumpWidget(buildTestWidget());
        await tester.pump();

        expect(
            find.text('No projects yet - create your first one!'), findsNothing);
      });

      testWidgets('shows project description when available', (tester) async {
        final projects = [
          Project(
            id: '1',
            name: 'Test Project',
            description: 'This is a test description',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
        ];
        when(mockProjectProvider.projects).thenReturn(projects);

        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.text('Test Project'), findsOneWidget);
        expect(find.text('This is a test description'), findsOneWidget);
      });
    });

    group('App Icon', () {
      testWidgets('shows analytics icon', (tester) async {
        await tester.pumpWidget(buildTestWidget());
        await tester.pumpAndSettle();

        expect(find.byIcon(Icons.analytics_outlined), findsOneWidget);
      });
    });
  });
}
