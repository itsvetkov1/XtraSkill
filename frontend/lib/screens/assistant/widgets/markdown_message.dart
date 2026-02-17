/// Markdown message widget for rendering AI responses with syntax highlighting.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/github.dart';
import 'package:flutter_highlight/themes/vs2015.dart';
import 'package:markdown/markdown.dart' as md;
import 'package:url_launcher/url_launcher.dart';

/// Widget that renders markdown content with syntax-highlighted code blocks
class MarkdownMessage extends StatelessWidget {
  /// Markdown content to render
  final String content;

  /// Whether content is currently streaming (for incremental rendering)
  final bool isStreaming;

  const MarkdownMessage({
    super.key,
    required this.content,
    this.isStreaming = false,
  });

  @override
  Widget build(BuildContext context) {
    // Handle edge case: empty content
    if (content.isEmpty) {
      return const SizedBox.shrink();
    }

    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return MarkdownBody(
      data: content,
      selectable: true,
      styleSheet: _buildStyleSheet(theme),
      builders: {
        'code': CodeElementBuilder(context, isDark),
      },
      onTapLink: (text, href, title) => _handleLinkTap(href),
    );
  }

  /// Builds markdown style sheet from theme
  MarkdownStyleSheet _buildStyleSheet(ThemeData theme) {
    return MarkdownStyleSheet(
      // Paragraphs
      p: theme.textTheme.bodyLarge?.copyWith(
        fontSize: 15,
        height: 1.4,
      ),

      // Headings
      h1: theme.textTheme.headlineMedium?.copyWith(
        fontWeight: FontWeight.bold,
      ),
      h2: theme.textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.bold,
      ),
      h3: theme.textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.bold,
      ),

      // Code
      code: TextStyle(
        fontFamily: 'monospace',
        fontSize: 14,
        backgroundColor: theme.colorScheme.surfaceContainerHighest,
        color: theme.colorScheme.onSurface,
      ),
      codeblockDecoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      codeblockPadding: const EdgeInsets.all(12),

      // Lists
      listBullet: theme.textTheme.bodyLarge?.copyWith(
        fontSize: 15,
        height: 1.4,
      ),

      // Blockquotes
      blockquote: theme.textTheme.bodyLarge?.copyWith(
        color: theme.colorScheme.onSurfaceVariant,
        fontStyle: FontStyle.italic,
      ),
      blockquoteDecoration: BoxDecoration(
        border: Border(
          left: BorderSide(
            color: theme.colorScheme.primary,
            width: 4,
          ),
        ),
      ),
      blockquotePadding: const EdgeInsets.only(left: 12),

      // Tables
      tableHead: theme.textTheme.bodyLarge?.copyWith(
        fontWeight: FontWeight.bold,
      ),
      tableBody: theme.textTheme.bodyLarge,
      tableBorder: TableBorder.all(
        color: theme.colorScheme.outlineVariant,
      ),
    );
  }

  /// Handles link taps - opens URLs via url_launcher
  Future<void> _handleLinkTap(String? href) async {
    if (href == null || href.isEmpty) return;

    final uri = Uri.tryParse(href);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}

/// Custom markdown element builder for syntax-highlighted code blocks
class CodeElementBuilder extends MarkdownElementBuilder {
  final BuildContext context;
  final bool isDark;

  CodeElementBuilder(this.context, this.isDark);

  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    final code = element.textContent;

    // Extract language from class attribute (e.g., "language-python" -> "python")
    String? language;
    final className = element.attributes['class'];
    if (className != null && className.startsWith('language-')) {
      language = className.substring('language-'.length);
    }

    final theme = Theme.of(context);
    final codeTheme = isDark ? vs2015Theme : githubTheme;

    return Stack(
      children: [
        // Syntax-highlighted code block
        Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(8),
          ),
          padding: const EdgeInsets.all(12),
          child: HighlightView(
            code,
            language: language ?? 'plaintext',
            theme: codeTheme,
            padding: EdgeInsets.zero,
            textStyle: const TextStyle(
              fontFamily: 'monospace',
              fontSize: 14,
            ),
          ),
        ),

        // Copy code button (top-right corner)
        Positioned(
          top: 4,
          right: 4,
          child: IconButton(
            icon: Icon(
              Icons.copy,
              size: 18,
              color: theme.colorScheme.onSurfaceVariant,
            ),
            tooltip: 'Copy code',
            padding: const EdgeInsets.all(4),
            constraints: const BoxConstraints(
              minWidth: 32,
              minHeight: 32,
            ),
            onPressed: () => _copyCode(code),
          ),
        ),
      ],
    );
  }

  /// Copies code to clipboard
  void _copyCode(String code) {
    try {
      Clipboard.setData(ClipboardData(text: code));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Code copied to clipboard'),
          duration: Duration(seconds: 2),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to copy code'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }
}
