import 'package:flutter/material.dart';
import 'package:pluto_grid/pluto_grid.dart';

/// Widget for displaying Excel/CSV content as an interactive table grid.
///
/// Features:
/// - PlutoGrid with sortable columns
/// - Virtualized rendering for 1000+ rows
/// - Metadata header showing row count and sheet names
class ExcelTableViewer extends StatefulWidget {
  final String content;
  final Map<String, dynamic> metadata;

  const ExcelTableViewer({
    super.key,
    required this.content,
    required this.metadata,
  });

  @override
  State<ExcelTableViewer> createState() => _ExcelTableViewerState();
}

class _ExcelTableViewerState extends State<ExcelTableViewer> {
  PlutoGridStateManager? stateManager;
  bool _isLoading = true;
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
