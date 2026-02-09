# Overview

This repository contains a minimal, local-first [Barefoot Data Platform](https://davidgasquez.com/barefoot-data-platforms/) used to analyze some of my personal data.

Input datasets need to be manually downloaded and placed into their respecive locations in the `inputs/` directory.  
Assets are defined in the `assets/` directory and can be written using either Python or SQL (evaluated using [chDB](https://clickhouse.com/chdb)).  
Dashboards are built using [Observable Framework](https://observablehq.com/framework/).

# Quickstart

- `uv run bdp list`
- `uv run bdp check`
- `uv run bdp materialize`
- `uv run bdp materialize raw.base_numbers`

# Acknowledgement

This repository was heavily inspired by David Gasquez [Barefoot Data Platform](https://github.com/davidgasquez/barefoot-data-platform) reference repository.
