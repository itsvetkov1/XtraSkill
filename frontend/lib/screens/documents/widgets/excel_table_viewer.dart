import 'package:flutter/material.dart';
import 'package:pluto_grid/pluto_grid.dart';

import '../../../services/document_service.dart';

/// Widget for displaying Excel/CSV content as an interactive table grid.
///
/// Features:
/// - PlutoGrid with sortable columns
/// - Virtualized rendering for 1000+ rows
/// - Metadata header showing row count and sheet names
class ExcelTableViewer extends StatefulWidget {
  final String content;
  final Map<String, dynamic> metadata;
  final String documentId;

  const ExcelTableViewer({
    super.key,
    required this.content,
    required this.metadata,
    required this.documentId,
  });

  @override
  State<ExcelTableViewer> createState() => _ExcelTableViewerState();
}

class _ExcelTableViewerState extends State<ExcelTableViewer> {
  PlutoGridStateManager? stateManager;
  bool _isLoading = true;
  bool _isExporting = false;
  String? _error;
  List<PlutoColumn> _columns = [];
  List<PlutoRow> _rows = [];

  @override
  void initState() {
    super.initState();
    _parseContent();
  }

  Future<void> _parseContent() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Parse tab-separated content from backend
      final lines = widget.content.split('\n').where((l) => l.isNotEmpty).toList();

      if (lines.isEmpty) {
        setState(() {
          _error = 'Empty content';
          _isLoading = false;
        });
        return;
      }

      // First line = headers
      final headerCells = lines[0].split('\t');

      // Build PlutoColumns
      final columns = headerCells.asMap().entries.map((entry) {
        return PlutoColumn(
          title: entry.value.isEmpty ? 'Column ${entry.key + 1}' : entry.value,
          field: 'field_${entry.key}',
          type: PlutoColumnType.text(),
          enableSorting: true,
        );
      }).toList();

      // Build PlutoRows from data lines
      final rows = <PlutoRow>[];
      for (var i = 1; i < lines.length; i++) {
        final cells = lines[i].split('\t');
        final rowCells = <String, PlutoCell>{};

        for (var j = 0; j < headerCells.length; j++) {
          final value = j < cells.length ? cells[j] : '';
          rowCells['field_$j'] = PlutoCell(value: value);
        }

        rows.add(PlutoRow(cells: rowCells));
      }

      setState(() {
        _columns = columns;
        _rows = rows;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to parse table: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _handleExport(BuildContext context, String format) async {
    setState(() => _isExporting = true);

    // Show loading snackbar
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
            ),
            const SizedBox(width: 12),
            Text('Exporting to ${format.toUpperCase()}...'),
          ],
        ),
        duration: const Duration(seconds: 30),
      ),
    );

    try {
      final service = DocumentService();
      await service.exportDocument(widget.documentId, format);

      if (!context.mounted) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.white),
              const SizedBox(width: 12),
              Text('Exported to ${format.toUpperCase()} successfully'),
            ],
          ),
          backgroundColor: Colors.green,
          duration: const Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.error, color: Colors.white),
              const SizedBox(width: 12),
              Expanded(child: Text('Export failed: $e')),
            ],
          ),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 4),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isExporting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(_error!),
          ],
        ),
      );
    }

    final sheetNames = widget.metadata['sheet_names'] as List<dynamic>?;
    final rowCount = widget.metadata['total_rows'] ??
                     widget.metadata['row_count'] ??
                     _rows.length;

    return Column(
      children: [
        // Metadata header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            border: Border(
              bottom: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
          ),
          child: Row(
            children: [
              Icon(Icons.table_chart, size: 18, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                '$rowCount rows',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (sheetNames != null && sheetNames.isNotEmpty) ...[
                const SizedBox(width: 16),
                const Text('•'),
                const SizedBox(width: 16),
                Text(
                  'Sheet: ${sheetNames.join(', ')}',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
              const Spacer(),
              // Export menu
              PopupMenuButton<String>(
                icon: Icon(
                  Icons.download_rounded,
                  color: Theme.of(context).colorScheme.primary,
                ),
                tooltip: 'Export original data',
                enabled: !_isExporting,
                onSelected: (format) => _handleExport(context, format),
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'xlsx',
                    child: Row(
                      children: [
                        Icon(Icons.table_chart, size: 20),
                        SizedBox(width: 12),
                        Text('Export to Excel (.xlsx)'),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'csv',
                    child: Row(
                      children: [
                        Icon(Icons.insert_drive_file, size: 20),
                        SizedBox(width: 12),
                        Text('Export to CSV'),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        // PlutoGrid
        Expanded(
          child: PlutoGrid(
            columns: _columns,
            rows: _rows,
            onLoaded: (PlutoGridOnLoadedEvent event) {
              stateManager = event.stateManager;
            },
            configuration: PlutoGridConfiguration(
              style: PlutoGridStyleConfig(
                enableGridBorderShadow: false,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
