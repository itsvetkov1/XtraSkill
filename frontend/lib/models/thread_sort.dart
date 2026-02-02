/// Sort options for thread lists.
library;

/// Available sort options for thread listings.
enum ThreadSortOption {
  newest('Newest'),
  oldest('Oldest'),
  alphabetical('A-Z');

  final String label;
  const ThreadSortOption(this.label);
}
