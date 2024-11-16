import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from faker import Faker

class SalesDataGenerator:
    def __init__(self, seed: Optional[int] = None):
        self.fake = Faker()
        if seed:
            random.seed(seed)
            np.random.seed(seed)
            Faker.seed(seed)
            
        # Load configuration data
        self.industry_data = {
            "Technology": ["SaaS", "Hardware", "IT Services"],
            "Manufacturing": ["Automotive", "Electronics", "Industrial"],
            "Healthcare": ["Hospitals", "Biotech", "Medical Devices"],
            "Financial": ["Banking", "Insurance", "Investment"]
        }
        
        self.expertise_areas = [
            "Technical", "Solution Selling", "Enterprise",
            "Consultative Selling", "SMB", "Transactional"
        ]
        
        self.products = self._generate_product_catalog()

    def _generate_product_catalog(self) -> List[Dict]:
        """Generate a realistic product catalog"""
        products = []
        categories = ["Software", "Hardware", "Services", "Consulting"]
        
        for category in categories:
            for i in range(random.randint(3, 6)):
                base_price = random.uniform(1000, 50000)
                product = {
                    "id": str(uuid.uuid4()),
                    "name": f"{category}-{self.fake.word().title()}-{i+1}",
                    "category": category,
                    "price": round(base_price, 2),
                    "description": self.fake.paragraph(),
                    "features": [self.fake.word() for _ in range(random.randint(3, 6))],
                    "customizationOptions": [
                        self.fake.word() for _ in range(random.randint(2, 4))
                    ],
                    "discountTiers": [
                        {
                            "quantity": qty,
                            "discountPercentage": disc
                        } for qty, disc in [
                            (5, 5), (10, 10), (20, 15), (50, 20)
                        ]
                    ]
                }
                products.append(product)
        return products

    def generate_person(self, is_customer: bool = True) -> Dict:
        """Generate a person (customer contact or sales person)"""
        gender = random.choice(['M', 'F'])
        first_name = self.fake.first_name_male() if gender == 'M' else self.fake.first_name_female()
        last_name = self.fake.last_name()
        
        person = {
            "id": str(uuid.uuid4()),
            "firstName": first_name,
            "lastName": last_name,
            "email": self.fake.email(),
            "phoneNumber": f"+{random.randint(1, 9)}{self.fake.msisdn()[1:]}",
            "role": random.choice([
                "CEO", "CTO", "Director", "Manager", "Senior Manager"
            ]) if is_customer else "Sales Representative",
            "demographics": {
                "nationality": self.fake.country(),
                "languages": random.sample(
                    ["English", "Spanish", "French", "German", "Chinese"],
                    k=random.randint(1, 3)
                ),
                "timezone": random.choice([
                    "UTC-8", "UTC-5", "UTC", "UTC+1", "UTC+8"
                ]),
                "preferredContactMethod": random.choice([
                    "email", "phone", "both"
                ])
            }
        }
        return person

    def generate_sales_person(self) -> Dict:
        """Generate a sales person with performance metrics"""
        base_person = self.generate_person(is_customer=False)
        
        # Add sales-specific attributes
        sales_person = {
            **base_person,
            "salesMetrics": {
                "quotaAttainment": round(random.uniform(0.6, 1.2), 2),
                "averageDealSize": round(random.uniform(10000, 100000), 2),
                "winRate": round(random.uniform(0.2, 0.4), 2),
                "averageSalesCycle": random.randint(30, 90)
            },
            "territories": random.sample(
                ["North America", "Europe", "Asia Pacific", "Latin America"],
                k=random.randint(1, 2)
            ),
            "expertise": random.sample(
                self.expertise_areas,
                k=random.randint(2, 4)
            )
        }
        return sales_person

    def generate_customer(self) -> Dict:
        """Generate a customer company with contacts"""
        industry = random.choice(list(self.industry_data.keys()))
        sub_industry = random.choice(self.industry_data[industry])
        
        size_category = random.choices(
            ["small", "medium", "enterprise"],
            weights=[0.5, 0.3, 0.2]
        )[0]
        
        # Generate company size-appropriate number of contacts
        num_contacts = {
            "small": random.randint(1, 3),
            "medium": random.randint(2, 5),
            "enterprise": random.randint(3, 8)
        }[size_category]
        
        customer = {
            "id": str(uuid.uuid4()),
            "company": self.fake.company(),
            "contacts": [
                self.generate_person(is_customer=True)
                for _ in range(num_contacts)
            ],
            "industry": f"{industry} - {sub_industry}",
            "size": size_category,
            "status": random.choice([
                "lead", "prospect", "qualified", "customer"
            ]),
            "annualRevenue": random.randint(1000000, 1000000000),
            "employeeCount": random.randint(10, 10000),
            "location": {
                "country": self.fake.country(),
                "city": self.fake.city(),
                "timezone": random.choice([
                    "UTC-8", "UTC-5", "UTC", "UTC+1", "UTC+8"
                ])
            }
        }
        return customer

    def generate_interaction(
        self,
        customer_id: str,
        sales_person_id: str,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """Generate a sales interaction"""
        if not timestamp:
            timestamp = datetime.now() - timedelta(
                days=random.randint(0, 365)
            )
            
        interaction = {
            "id": str(uuid.uuid4()),
            "type": random.choice([
                "call", "email", "meeting", "demo", "proposal"
            ]),
            "timestamp": timestamp.isoformat(),
            "customerId": customer_id,
            "salesPersonId": sales_person_id,
            "duration": random.randint(5, 120),
            "outcome": random.choice([
                "successful", "followupRequired", 
                "notInterested", "noAnswer"
            ]),
            "notes": self.fake.paragraph(),
            "nextSteps": self.fake.sentence(),
            "sentiment": random.choice([
                "positive", "neutral", "negative"
            ]),
            "topics": random.sample([
                "pricing", "features", "timeline", "technical",
                "competition", "implementation", "support"
            ], k=random.randint(1, 4))
        }
        return interaction

    def generate_opportunity(
        self,
        customer_id: str,
        sales_person_id: str
    ) -> Dict:
        """Generate a sales opportunity"""
        # Select random products for this opportunity
        num_products = random.randint(1, 4)
        selected_products = random.sample(self.products, k=num_products)
        
        status = random.choice([
            "identified", "qualified", "proposalSent",
            "negotiating", "won", "lost"
        ])
        
        opportunity = {
            "id": str(uuid.uuid4()),
            "customerId": customer_id,
            "salesPersonId": sales_person_id,
            "products": [
                {
                    "productId": product["id"],
                    "quantity": random.randint(1, 10),
                    "customizations": random.sample(
                        product["customizationOptions"],
                        k=random.randint(
                            0,
                            len(product["customizationOptions"])
                        )
                    ),
                    "appliedDiscount": random.uniform(0, 0.2)
                }
                for product in selected_products
            ],
            "status": status,
            "value": round(random.uniform(10000, 1000000), 2),
            "probability": round(random.uniform(0.1, 0.9), 2),
            "expectedCloseDate": (
                datetime.now() + timedelta(days=random.randint(30, 180))
            ).strftime('%Y-%m-%d'),
            "lossReason": self.fake.sentence() if status == "lost" else None,
            "competitorInvolved": self.fake.company() if random.random() > 0.5 else None
        }
        return opportunity

    def generate_dataset(
        self,
        num_customers: int = 100,
        num_sales_people: int = 10
    ) -> Dict:
        """Generate a complete synthetic sales dataset"""
        # Generate base data
        sales_people = [
            self.generate_sales_person()
            for _ in range(num_sales_people)
        ]
        customers = [
            self.generate_customer()
            for _ in range(num_customers)
        ]
        
        # Generate opportunities and interactions
        opportunities = []
        interactions = []
        
        for customer in customers:
            # Assign random sales person
            sales_person = random.choice(sales_people)
            
            # Generate 0-3 opportunities per customer
            num_opportunities = random.randint(0, 3)
            for _ in range(num_opportunities):
                opportunity = self.generate_opportunity(
                    customer["id"],
                    sales_person["id"]
                )
                opportunities.append(opportunity)
                
                # Generate 2-8 interactions per opportunity
                num_interactions = random.randint(2, 8)
                for _ in range(num_interactions):
                    interaction = self.generate_interaction(
                        customer["id"],
                        sales_person["id"]
                    )
                    interactions.append(interaction)
        
        dataset = {
            "salesPeople": sales_people,
            "customers": customers,
            "opportunities": opportunities,
            "interactions": interactions,
            "products": self.products
        }
        return dataset

    def save_to_json(
        self,
        dataset: Dict,
        filename: str = "sales_data.json"
    ) -> None:
        """Save the generated dataset to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(dataset, f, indent=2)

    def save_to_csv(
        self,
        dataset: Dict,
        base_filename: str = "sales_data"
    ) -> None:
        """Save the generated dataset to separate CSV files"""
        for key, data in dataset.items():
            df = pd.DataFrame(data)
            df.to_csv(f"{base_filename}_{key}.csv", index=False)

# Usage example
if __name__ == "__main__":
    # Initialize generator with seed for reproducibility
    generator = SalesDataGenerator(seed=42)
    
    # Generate dataset
    dataset = generator.generate_dataset(
        num_customers=100,
        num_sales_people=10
    )
    
    # Save to JSON and CSV
    generator.save_to_json(dataset)
    generator.save_to_csv(dataset)
