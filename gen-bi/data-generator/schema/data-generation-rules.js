// Data Generation Rules and Patterns for Sales System

const dataGenerationRules = {
  // Person/Contact Generation Rules
  person: {
    namePatterns: {
      firstNames: {
        distribution: [
          { value: "common_western", weight: 0.4 },
          { value: "common_asian", weight: 0.3 },
          { value: "common_hispanic", weight: 0.2 },
          { value: "other", weight: 0.1 }
        ],
        rules: {
          // Ensure names match demographic patterns
          matchNationality: true,
          // 20% chance of having middle name
          includeMiddleName: 0.2
        }
      },
      emailGeneration: {
        patterns: [
          { pattern: "firstname.lastname@company.com", weight: 0.4 },
          { pattern: "f.lastname@company.com", weight: 0.3 },
          { pattern: "firstnamel@company.com", weight: 0.2 },
          { pattern: "custom_pattern", weight: 0.1 }
        ]
      }
    },
    demographics: {
      nationality: {
        // Distribution should match your target market
        distribution: [
          { value: "US", weight: 0.3 },
          { value: "UK", weight: 0.15 },
          { value: "Germany", weight: 0.1 },
          { value: "France", weight: 0.1 },
          { value: "Japan", weight: 0.1 },
          { value: "China", weight: 0.15 },
          { value: "Other", weight: 0.1 }
        ]
      },
      languages: {
        rules: {
          // Min/max languages per person
          minLanguages: 1,
          maxLanguages: 3,
          // Probability of speaking English as non-native
          englishProbability: 0.8,
          // Probability of speaking local language
          localLanguageProbability: 0.95
        }
      }
    }
  },

  // Customer Generation Rules
  customer: {
    companyAttributes: {
      size: {
        distribution: [
          { value: "small", weight: 0.5, 
            rules: { 
              employeeRange: [10, 100],
              revenueRange: [1000000, 10000000]
            }
          },
          { value: "medium", weight: 0.3,
            rules: {
              employeeRange: [101, 1000],
              revenueRange: [10000001, 100000000]
            }
          },
          { value: "enterprise", weight: 0.2,
            rules: {
              employeeRange: [1001, 50000],
              revenueRange: [100000001, 1000000000]
            }
          }
        ]
      },
      industry: {
        // Industry distribution with sub-industry probabilities
        distribution: {
          "Technology": {
            weight: 0.3,
            subIndustries: [
              { value: "SaaS", weight: 0.4 },
              { value: "Hardware", weight: 0.3 },
              { value: "IT Services", weight: 0.3 }
            ]
          },
          "Manufacturing": {
            weight: 0.2,
            subIndustries: [
              { value: "Automotive", weight: 0.3 },
              { value: "Electronics", weight: 0.4 },
              { value: "Industrial", weight: 0.3 }
            ]
          }
          // Add more industries as needed
        }
      }
    },
    contactGeneration: {
      rules: {
        // Number of contacts per company based on size
        small: { min: 1, max: 3 },
        medium: { min: 2, max: 5 },
        enterprise: { min: 3, max: 8 },
        // Role distribution
        roles: [
          { value: "C-Level", weight: 0.1 },
          { value: "Director", weight: 0.2 },
          { value: "Manager", weight: 0.4 },
          { value: "Individual Contributor", weight: 0.3 }
        ]
      }
    }
  },

  // Sales Person Generation Rules
  salesPerson: {
    metrics: {
      quotaAttainment: {
        distribution: "normalDistribution",
        mean: 0.85,
        stdDev: 0.15,
        min: 0.4,
        max: 1.5
      },
      winRate: {
        distribution: "normalDistribution",
        mean: 0.25,
        stdDev: 0.08,
        min: 0.1,
        max: 0.4
      },
      averageSalesCycle: {
        // Days to close
        distribution: "normalDistribution",
        mean: 60,
        stdDev: 15,
        min: 30,
        max: 120
      }
    },
    expertise: {
      // Probability of expertise combinations
      rules: {
        minExpertise: 2,
        maxExpertise: 4,
        combinations: [
          {
            set: ["Technical", "Solution Selling"],
            probability: 0.3
          },
          {
            set: ["Enterprise", "Consultative Selling"],
            probability: 0.25
          },
          {
            set: ["SMB", "Transactional"],
            probability: 0.25
          }
        ]
      }
    }
  },

  // Interaction Generation Rules
  interaction: {
    frequency: {
      // Interactions per opportunity stage
      rules: {
        identified: { min: 1, max: 2 },
        qualified: { min: 2, max: 4 },
        proposalSent: { min: 3, max: 6 },
        negotiating: { min: 4, max: 8 }
      }
    },
    patterns: {
      // Time between interactions based on stage
      timingRules: {
        identified: { minDays: 1, maxDays: 5 },
        qualified: { minDays: 3, maxDays: 10 },
        proposalSent: { minDays: 2, maxDays: 7 },
        negotiating: { minDays: 1, maxDays: 4 }
      },
      // Type distribution by stage
      typeDistribution: {
        identified: [
          { type: "email", weight: 0.6 },
          { type: "call", weight: 0.4 }
        ],
        qualified: [
          { type: "call", weight: 0.4 },
          { type: "email", weight: 0.3 },
          { type: "meeting", weight: 0.3 }
        ],
        proposalSent: [
          { type: "meeting", weight: 0.4 },
          { type: "email", weight: 0.4 },
          { type: "call", weight: 0.2 }
        ]
      }
    },
    sentiment: {
      // Sentiment progression rules
      rules: {
        initialDistribution: [
          { value: "positive", weight: 0.6 },
          { value: "neutral", weight: 0.3 },
          { value: "negative", weight: 0.1 }
        ],
        progressionPatterns: {
          positive: {
            stayPositive: 0.7,
            toNeutral: 0.25,
            toNegative: 0.05
          },
          neutral: {
            toPositive: 0.4,
            stayNeutral: 0.4,
            toNegative: 0.2
          }
        }
      }
    }
  },

  // Opportunity Generation Rules
  opportunity: {
    lifecycle: {
      // Stage progression probabilities
      stageProgression: {
        identified: {
          toQualified: 0.6,
          toLost: 0.4
        },
        qualified: {
          toProposalSent: 0.7,
          toLost: 0.3
        },
        proposalSent: {
          toNegotiating: 0.6,
          toLost: 0.4
        },
        negotiating: {
          toWon: 0.7,
          toLost: 0.3
        }
      },
      // Duration in each stage (days)
      stageDuration: {
        identified: { min: 1, max: 7 },
        qualified: { min: 5, max: 20 },
        proposalSent: { min: 3, max: 14 },
        negotiating: { min: 5, max: 30 }
      }
    },
    products: {
      // Product combination rules
      rules: {
        minProducts: 1,
        maxProducts: 5,
        // Probability of additional products
        crossSellProbability: 0.4,
        // Common product combinations
        commonBundles: [
          {
            products: ["ProductA", "ProductB"],
            probability: 0.3,
            averageDiscount: 0.1
          },
          {
            products: ["ProductC", "ProductD", "ProductE"],
            probability: 0.2,
            averageDiscount: 0.15
          }
        ]
      }
    },
    value: {
      // Deal value calculation rules
      rules: {
        baseValueRange: {
          small: { min: 10000, max: 50000 },
          medium: { min: 50001, max: 200000 },
          enterprise: { min: 200001, max: 1000000 }
        },
        multipliers: {
          industryMultipliers: {
            "Technology": 1.2,
            "Manufacturing": 1.1,
            "Healthcare": 1.3
          },
          urgencyMultipliers: {
            high: 1.1,
            medium: 1.0,
            low: 0.9
          }
        }
      }
    }
  }
};
