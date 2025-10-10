#!/usr/bin/env python3
"""
AI Code Refactoring Cost Estimator
Estimates costs for using various AI models for code analysis and refactoring.

Use the howManyTokens.py script available in the project to determine the approximate number of tokens in your project.
Then this script can be used to determine how much it would cost to refactor.

The purpose of the script was simply to determine the cost overhead of refactoring using a larger model.
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, Tuple, List
from dataclasses import dataclass


# ============================================================================
# CONFIGURATION - Adjust these assumptions as needed
# ============================================================================

@dataclass
class ModelPricing:
    """Pricing structure for AI models (per million tokens)"""
    name: str
    input_cost: float
    output_cost: float
    cached_input_cost: float = 0.0  # Cost for cached context (if supported)
    supports_caching: bool = False
    
    def format_costs(self) -> str:
        """Format pricing info for display"""
        lines = [f"  Input:  ${self.input_cost:.2f}/M tokens"]
        lines.append(f"  Output: ${self.output_cost:.2f}/M tokens")
        if self.supports_caching:
            lines.append(f"  Cached: ${self.cached_input_cost:.2f}/M tokens (90% reduction)")
        return "\n".join(lines)


# Model pricing database (as of October 2025)
MODELS = {
    'sonnet-4.5': ModelPricing(
        name='Claude Sonnet 4.5',
        input_cost=3.00,
        output_cost=15.00,
        cached_input_cost=0.30,
        supports_caching=True
    ),
    'opus-4': ModelPricing(
        name='Claude Opus 4',
        input_cost=15.00,
        output_cost=75.00,
        cached_input_cost=1.50,
        supports_caching=True
    ),
    'gpt-4-turbo': ModelPricing(
        name='GPT-4 Turbo',
        input_cost=10.00,
        output_cost=30.00,
        cached_input_cost=1.00,
        supports_caching=True
    ),
    'gpt-4o': ModelPricing(
        name='GPT-4o',
        input_cost=2.50,
        output_cost=10.00,
        cached_input_cost=1.25,
        supports_caching=True
    ),
    'gpt-3.5-turbo': ModelPricing(
        name='GPT-3.5 Turbo',
        input_cost=0.50,
        output_cost=1.50,
        supports_caching=False
    ),
    'grok-2-fast': ModelPricing(
        name='Grok 2 Fast',
        input_cost=5.00,
        output_cost=15.00,
        supports_caching=False
    ),
    'grok-code-fast': ModelPricing(
        name='Grok Code Fast',
        input_cost=4.00,
        output_cost=12.00,
        supports_caching=False
    ),
}

# Phase assumptions
PHASE_CONFIG = {
    'analysis': {
        'description': 'Initial codebase analysis and understanding',
        'iterations': 2,
        'avg_output_tokens': 4000,
        'instruction_tokens': 500,
    },
    'planning': {
        'description': 'Architecture review and refactoring plan creation',
        'iterations': 3,
        'avg_output_tokens': 5000,
        'instruction_tokens': 1000,
    },
    'execution': {
        'description': 'Code refactoring implementation',
        'iterations': None,  # Will be user input
        'avg_output_tokens': 3500,
        'instruction_tokens': 2000,
    },
    'review': {
        'description': 'Code review, testing, and refinement',
        'iterations': 4,
        'avg_output_tokens': 2500,
        'instruction_tokens': 800,
    },
}


# ============================================================================
# COST CALCULATOR
# ============================================================================

class CostEstimator:
    """Calculate AI refactoring costs"""
    
    def __init__(self, project_tokens: int, refactor_percent: float, 
                 execution_iterations: int, model: ModelPricing, use_caching: bool):
        self.project_tokens = project_tokens
        self.refactor_percent = refactor_percent
        self.execution_iterations = execution_iterations
        self.model = model
        self.use_caching = use_caching and model.supports_caching
        self.phase_results = {}
        
    def calculate_phase_cost(self, phase_name: str, config: Dict) -> Tuple[float, float, int, int]:
        """
        Calculate cost for a single phase
        Returns: (input_cost, output_cost, total_input_tokens, total_output_tokens)
        """
        iterations = config['iterations']
        if iterations is None:  # Execution phase
            iterations = self.execution_iterations
        
        # Calculate tokens per iteration
        input_per_iter = self.project_tokens + config['instruction_tokens']
        output_per_iter = config['avg_output_tokens']
        
        # Total tokens
        total_input_tokens = input_per_iter * iterations
        total_output_tokens = output_per_iter * iterations
        
        # Calculate costs
        if self.use_caching and iterations > 1:
            # First iteration: full cost
            first_iter_cost = (input_per_iter / 1_000_000) * self.model.input_cost
            # Subsequent iterations: cached cost (90% reduction on project tokens)
            cached_tokens = self.project_tokens
            uncached_tokens = config['instruction_tokens']
            subsequent_cost_per_iter = (
                (cached_tokens / 1_000_000) * self.model.cached_input_cost +
                (uncached_tokens / 1_000_000) * self.model.input_cost
            )
            input_cost = first_iter_cost + (subsequent_cost_per_iter * (iterations - 1))
        else:
            # No caching: full cost for all iterations
            input_cost = (total_input_tokens / 1_000_000) * self.model.input_cost
        
        output_cost = (total_output_tokens / 1_000_000) * self.model.output_cost
        
        return input_cost, output_cost, total_input_tokens, total_output_tokens
    
    def calculate_all_phases(self) -> Dict:
        """Calculate costs for all phases"""
        total_input_cost = 0
        total_output_cost = 0
        total_input_tokens = 0
        total_output_tokens = 0
        
        for phase_name, config in PHASE_CONFIG.items():
            input_cost, output_cost, input_tokens, output_tokens = self.calculate_phase_cost(
                phase_name, config
            )
            
            self.phase_results[phase_name] = {
                'description': config['description'],
                'iterations': config['iterations'] if config['iterations'] else self.execution_iterations,
                'input_cost': input_cost,
                'output_cost': output_cost,
                'total_cost': input_cost + output_cost,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
            }
            
            total_input_cost += input_cost
            total_output_cost += output_cost
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
        
        return {
            'total_input_cost': total_input_cost,
            'total_output_cost': total_output_cost,
            'total_cost': total_input_cost + total_output_cost,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
        }


# ============================================================================
# REPORT FORMATTING
# ============================================================================

def format_report(estimator: CostEstimator, totals: Dict, project_tokens: int, 
                  refactor_percent: float) -> str:
    """Format the cost estimation report"""
    lines = []
    lines.append("=" * 90)
    lines.append("AI CODE REFACTORING COST ESTIMATION REPORT")
    lines.append("=" * 90)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Project Info
    lines.append("PROJECT INFORMATION")
    lines.append("-" * 90)
    lines.append(f"Total project tokens:      {project_tokens:,}")
    lines.append(f"Refactoring scope:         {refactor_percent:.1f}% (~{int(project_tokens * refactor_percent / 100):,} tokens)")
    lines.append(f"Execution iterations:      {estimator.execution_iterations}")
    lines.append("")
    
    # Model Info
    lines.append("MODEL CONFIGURATION")
    lines.append("-" * 90)
    lines.append(f"Model: {estimator.model.name}")
    lines.append(estimator.model.format_costs())
    lines.append(f"Context caching: {'ENABLED' if estimator.use_caching else 'DISABLED'}")
    if not estimator.model.supports_caching and estimator.use_caching:
        lines.append("  (Note: This model does not support context caching)")
    lines.append("")
    
    # Phase Breakdown
    lines.append("COST BREAKDOWN BY PHASE")
    lines.append("-" * 90)
    lines.append(f"{'Phase':<20} {'Iterations':>12} {'Input $':>12} {'Output $':>12} {'Total $':>12}")
    lines.append("-" * 90)
    
    for phase_name, results in estimator.phase_results.items():
        lines.append(
            f"{phase_name.capitalize():<20} "
            f"{results['iterations']:>12} "
            f"${results['input_cost']:>11.3f} "
            f"${results['output_cost']:>11.3f} "
            f"${results['total_cost']:>11.3f}"
        )
    
    lines.append("-" * 90)
    lines.append(
        f"{'TOTAL':<20} "
        f"{sum(r['iterations'] for r in estimator.phase_results.values()):>12} "
        f"${totals['total_input_cost']:>11.3f} "
        f"${totals['total_output_cost']:>11.3f} "
        f"${totals['total_cost']:>11.3f}"
    )
    lines.append("")
    
    # Detailed Phase Information
    lines.append("DETAILED PHASE INFORMATION")
    lines.append("-" * 90)
    for phase_name, results in estimator.phase_results.items():
        lines.append(f"\n{phase_name.upper()}: {results['description']}")
        lines.append(f"  Iterations:    {results['iterations']}")
        lines.append(f"  Input tokens:  {results['input_tokens']:,}")
        lines.append(f"  Output tokens: {results['output_tokens']:,}")
        lines.append(f"  Cost:          ${results['total_cost']:.3f}")
    lines.append("")
    
    # Summary
    lines.append("COST SUMMARY")
    lines.append("-" * 90)
    lines.append(f"Total Input Cost:    ${totals['total_input_cost']:.2f}")
    lines.append(f"Total Output Cost:   ${totals['total_output_cost']:.2f}")
    lines.append(f"TOTAL PROJECT COST:  ${totals['total_cost']:.2f}")
    lines.append("")
    lines.append(f"Total Input Tokens:  {totals['total_input_tokens']:,}")
    lines.append(f"Total Output Tokens: {totals['total_output_tokens']:,}")
    lines.append(f"Total Tokens:        {totals['total_input_tokens'] + totals['total_output_tokens']:,}")
    lines.append("")
    
    # Cost comparison
    if estimator.model.supports_caching:
        if estimator.use_caching:
            # Show cost without caching
            estimator_no_cache = CostEstimator(
                project_tokens, refactor_percent, 
                estimator.execution_iterations, estimator.model, False
            )
            totals_no_cache = estimator_no_cache.calculate_all_phases()
            savings = totals_no_cache['total_cost'] - totals['total_cost']
            savings_pct = (savings / totals_no_cache['total_cost']) * 100
            
            lines.append("CONTEXT CACHING ANALYSIS")
            lines.append("-" * 90)
            lines.append(f"Cost without caching:  ${totals_no_cache['total_cost']:.2f}")
            lines.append(f"Cost with caching:     ${totals['total_cost']:.2f}")
            lines.append(f"Savings:               ${savings:.2f} ({savings_pct:.1f}% reduction)")
        else:
            # Show potential savings with caching
            estimator_cache = CostEstimator(
                project_tokens, refactor_percent, 
                estimator.execution_iterations, estimator.model, True
            )
            totals_cache = estimator_cache.calculate_all_phases()
            savings = totals['total_cost'] - totals_cache['total_cost']
            savings_pct = (savings / totals['total_cost']) * 100
            
            lines.append("CONTEXT CACHING ANALYSIS")
            lines.append("-" * 90)
            lines.append(f"Current cost (no caching):  ${totals['total_cost']:.2f}")
            lines.append(f"Potential cost (caching):   ${totals_cache['total_cost']:.2f}")
            lines.append(f"Potential savings:          ${savings:.2f} ({savings_pct:.1f}% reduction)")
            lines.append("\n💡 TIP: Enable context caching to reduce costs!")
    
    lines.append("")
    lines.append("=" * 90)
    
    return "\n".join(lines)


def format_multi_model_comparison(project_tokens: int, refactor_percent: float,
                                  execution_iterations: int, use_caching: bool) -> str:
    """Generate comparison across all models"""
    lines = []
    lines.append("\n" + "=" * 90)
    lines.append("MULTI-MODEL COST COMPARISON")
    lines.append("=" * 90)
    lines.append(f"{'Model':<25} {'Caching':>10} {'Total Cost':>15} {'Input Cost':>15} {'Output Cost':>15}")
    lines.append("-" * 90)
    
    results = []
    for model_key, model in MODELS.items():
        estimator = CostEstimator(
            project_tokens, refactor_percent, 
            execution_iterations, model, use_caching
        )
        totals = estimator.calculate_all_phases()
        results.append((model.name, totals['total_cost'], totals['total_input_cost'], 
                       totals['total_output_cost'], use_caching and model.supports_caching))
    
    # Sort by total cost
    results.sort(key=lambda x: x[1])
    
    for name, total, input_cost, output_cost, caching in results:
        cache_status = "Yes" if caching else "No"
        lines.append(
            f"{name:<25} {cache_status:>10} ${total:>14.2f} ${input_cost:>14.2f} ${output_cost:>14.2f}"
        )
    
    lines.append("=" * 90)
    return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Estimate costs for AI-powered code refactoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available models:
{chr(10).join(f"  • {key}: {model.name}" for key, model in MODELS.items())}

Examples:
  python cost_estimator.py -t 51000 -r 20
  python cost_estimator.py -t 100000 -r 30 -m opus-4 --caching
  python cost_estimator.py -t 51000 -r 20 -i 15 --all-models
        """
    )
    
    parser.add_argument(
        '-t', '--tokens',
        type=int,
        required=True,
        help='Total project tokens (from token counter analysis)'
    )
    parser.add_argument(
        '-r', '--refactor-percent',
        type=float,
        required=True,
        help='Percentage of code to refactor (0-100)'
    )
    parser.add_argument(
        '-i', '--iterations',
        type=int,
        default=None,
        help='Number of execution iterations (default: prompt for input)'
    )
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='sonnet-4.5',
        choices=list(MODELS.keys()),
        help='AI model to use (default: sonnet-4.5)'
    )
    parser.add_argument(
        '--caching',
        action='store_true',
        help='Enable context caching (if supported by model)'
    )
    parser.add_argument(
        '--all-models',
        action='store_true',
        help='Show cost comparison across all models'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.tokens <= 0:
        print("ERROR: Token count must be positive")
        sys.exit(1)
    
    if not 0 < args.refactor_percent <= 100:
        print("ERROR: Refactor percentage must be between 0 and 100")
        sys.exit(1)
    
    # Get execution iterations
    if args.iterations is None:
        try:
            user_input = input("\nNumber of execution iterations (hit Enter for default of 10): ").strip()
            execution_iterations = int(user_input) if user_input else 10
        except ValueError:
            print("Invalid input. Using default of 10 iterations.")
            execution_iterations = 10
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)
    else:
        execution_iterations = args.iterations
    
    if execution_iterations <= 0:
        print("ERROR: Iterations must be positive")
        sys.exit(1)
    
    print(f"\n🤖 Calculating costs for {args.model}...")
    
    # Get model
    model = MODELS[args.model]
    
    # Calculate costs
    estimator = CostEstimator(
        args.tokens, 
        args.refactor_percent, 
        execution_iterations,
        model,
        args.caching
    )
    totals = estimator.calculate_all_phases()
    
    # Generate report
    report = format_report(estimator, totals, args.tokens, args.refactor_percent)
    
    # Add multi-model comparison if requested
    if args.all_models:
        comparison = format_multi_model_comparison(
            args.tokens, args.refactor_percent, 
            execution_iterations, args.caching
        )
        report += "\n" + comparison
    
    # Display report
    print(report)
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"cost_estimate_{args.model}_{timestamp}.txt"
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n💾 Report saved to: {log_file}")
    except Exception as e:
        print(f"\n❌ Failed to save report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()