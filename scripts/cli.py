#!/usr/bin/env python3
import argparse
import os
import sys

# Add the script's directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from data_generator import SalesDataGenerator

def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic sales data with customizable parameters'
    )
    
    parser.add_argument(
        '--customers', 
        type=int, 
        default=100,
        help='Number of customers to generate (default: 100)'
    )
    
    parser.add_argument(
        '--sales-people', 
        type=int, 
        default=10,
        help='Number of sales people to generate (default: 10)'
    )
    
    parser.add_argument(
        '--seed', 
        type=int,
        help='Random seed for reproducible data generation'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--output',
        default='sales_data',
        help='Base name for output files (default: sales_data)'
    )

    args = parser.parse_args()

    # Initialize generator
    generator = SalesDataGenerator(seed=args.seed)
    
    # Generate dataset
    dataset = generator.generate_dataset(
        num_customers=args.customers,
        num_sales_people=args.sales_people
    )
    
    # Save output based on format
    if args.format in ['json', 'both']:
        json_file = f"{args.output}.json"
        generator.save_to_json(dataset, json_file)
        print(f"JSON data saved to {json_file}")
        
    if args.format in ['csv', 'both']:
        generator.save_to_csv(dataset, args.output)
        print(f"CSV files saved with prefix {args.output}")

if __name__ == "__main__":
    main()
