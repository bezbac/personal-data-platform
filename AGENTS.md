## Tech Stack

- **Data Pipeline**: Custom `bdp` (barefoot data platform) system
- **Database**: None, using chDB via `bdp` for SQL execution
- **Data Format**: Parquet files
- **Query Language**: SQL with Jinja2-style templating
  (`{{ ref("dependency") }}`)
- **Visualization**: Observable Framework (see `observable/` subdirectory)

## Project Structure

```
<root>/
├── assets/
│   ├── *.sql               # SQL queries defining data transformations
│   ├── *.py                # Python asset generators
│   └── *.parquet           # Generated data files (git-ignored)
├── observable/             # Observable Framework visualization
│   ├── src/
│   │   ├── *.md            # Observable notebooks
│   │   └── assets/         # Symlinked parquet files
│   └── package.json
├── Makefile                # Build automation
└── pyproject.toml          # Python dependencies
```

## Data Pipeline

SQL queries in `/assets/` define data transformations following this pattern:

```sql
-- asset.name = filename_without_extension
-- asset.description = Human readable description
-- asset.depends = dependency_name

SELECT ...
FROM {{ ref("dependency_name") }}
```

### Dependency Resolution

- Queries reference dependencies using `{{ ref("name") }}`
- Pipeline automatically resolves and materializes dependencies in correct order

### Asset Types

1. **SQL-based assets**: Define transformations using SQL queries
2. **Python-based assets**: Define custom Python functions that return
   DataFrames

## Common Commands

Reference the Makefile for common commands.

## Adding New Data Sources

1. Create a new `.sql` file in `/assets/`
2. Add asset metadata as SQL comments:
   ```sql
   -- asset.name = my_new_asset
   -- asset.description = What this asset contains
   -- asset.depends = parent_asset
   ```
3. Write the SQL query using `{{ ref("dependency") }}` for dependencies
4. Run `make run` to generate the parquet file
5. Reference the parquet in Observable using
   `FileAttachment("assets/my_new_asset.parquet")`

## Python Environment

Uses `uv` for Python dependency management:

- Dependencies defined in `pyproject.toml`
- Virtual environment automatically managed
- Run commands with `uv run <command>`

## Observable Integration

Parquet files are symlinked into `observable/src/assets/` for use in
visualizations. See `observable/AGENTS.md` for Observable-specific
documentation.
