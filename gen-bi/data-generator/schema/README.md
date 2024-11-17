## Schemas to Model Outbound Sales Data 
A comprehensive set of JSON schemas that model an outbound sales system with the following key components:

1. **Person** (Base Schema):
   - Common attributes for both customers and sales people
   - Demographics including nationality and languages
   - Contact preferences

2. **Customer**:
   - Company information
   - Multiple contacts within the company
   - Industry and size classification
   - Location and timezone data

3. **SalesPerson**:
   - Extends the person schema
   - Performance metrics
   - Territories and expertise areas
   - Success rates and metrics

4. **Product**:
   - Detailed product information
   - Customization options
   - Pricing and discount tiers
   - Features and categories

5. **Interaction**:
   - All types of communications (calls, emails, meetings)
   - Duration and outcomes
   - Sentiment analysis
   - Notes and next steps
   - Topics discussed

6. **Opportunity**:
   - Sales pipeline tracking
   - Product combinations
   - Status and probability
   - Value and closing information
   - Competitive intelligence

This schema structure allows you to generate synthetic data that can help train AI models to:
1. Identify patterns in successful sales
2. Recommend next best actions
3. Match salespeople with prospects
4. Optimize contact timing
5. Suggest product combinations
6. Identify decision makers
