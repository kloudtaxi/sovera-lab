# Sales Data Generator CLI

A command-line interface for generating synthetic sales data including customers, sales people, products, opportunities, and interactions.

## Installation

Ensure you have Python 3.x installed and the required dependencies:
```bash
pip install faker numpy pandas
```

## Usage

```bash
./cli.py [options]
```

### Options

- `--customers NUMBER`: Number of customers to generate (default: 100)
- `--sales-people NUMBER`: Number of sales people to generate (default: 10)
- `--seed NUMBER`: Random seed for reproducible data generation
- `--format {json,csv,both}`: Output format (default: json)
- `--output NAME`: Base name for output files (default: sales_data)

### Examples

1. Generate default dataset in JSON format:
```bash
./cli.py
```

2. Generate dataset with specific number of customers and sales people:
```bash
./cli.py --customers 200 --sales-people 20
```

3. Generate dataset in both JSON and CSV formats with custom output name:
```bash
./cli.py --format both --output my_sales_data
```

4. Generate reproducible dataset using seed:
```bash
./cli.py --seed 42
```

## Output

### JSON Format
When using JSON format (default), the script generates a single file containing all data:
- `<output>.json`: Contains all generated data in a single JSON file

### CSV Format
When using CSV format, the script generates separate files for each data type:
- `<output>_salesPeople.csv`: Sales representatives data
- `<output>_customers.csv`: Customer companies and contacts
- `<output>_opportunities.csv`: Sales opportunities
- `<output>_interactions.csv`: Sales interactions
- `<output>_products.csv`: Product catalog

## Generated Data

The synthetic dataset includes:

1. **Products**
   - Categories: Software, Hardware, Services, Consulting
   - Includes pricing, features, and discount tiers

2. **Sales People**
   - Personal details and contact information
   - Performance metrics and territories
   - Areas of expertise

3. **Customers**
   - Company profiles with industry classification
   - Multiple contact persons
   - Size and revenue information

4. **Interactions**
   - Various types (calls, emails, meetings)
   - Includes duration, outcomes, and sentiment
   - Notes and next steps

5. **Opportunities**
   - Product selections and quantities
   - Status tracking and probability estimates
   - Value and timeline information
