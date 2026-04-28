"""
Example script demonstrating the Router → Extractor → Reasoner pattern.
This shows how the system efficiently filters data through multiple LLM calls.

To run:
    python scripts/demo_router_extractor_reasoner.py
"""

import asyncio
import json
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent.router import DataRouter
from backend.agent.data_extractor import DataExtractor
from backend.config import get_settings
from backend.intelligence.data_loader import load_all_data


async def demo_routing_pattern():
    """Demonstrate the Router → Extractor → Reasoner pattern."""
    
    settings = get_settings()
    api_key = settings.groq_api_key
    
    if not api_key:
        print("❌ GROQ_API_KEY not set in .env")
        return
    
    print("=" * 70)
    print("🚀 Router → Extractor → Reasoner Demo")
    print("=" * 70)
    
    # Initialize components
    router = DataRouter(api_key=api_key, router_model="llama-3.1-8b-instant")
    extractor = DataExtractor()
    all_data = load_all_data()
    
    # Example queries to test
    queries = [
        "How are mutual funds performing compared to direct stocks?",
        "Tell me about tech stocks and their sector performance.",
        "What's happening with banking sector stocks?",
        "Analyze my portfolio against current market trends.",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'─' * 70}")
        print(f"📌 Query {i}: {query}")
        print(f"{'─' * 70}")
        
        # STEP 1: Router - Small, fast model determines data needs
        print("\n[STEP 1] 🔄 Router: Analyzing query to determine data needs...")
        routing_decision = await router.route_query(query)
        print(f"  Routing Decision:")
        print(f"  {json.dumps(routing_decision, indent=2)}")
        
        # STEP 2: Extractor - Filter data based on routing
        print(f"\n[STEP 2] 🔍 Extractor: Filtering data based on routing decision...")
        filtered_data_json = extractor.extract(routing_decision, all_data)
        filtered_size = len(filtered_data_json)
        total_size = len(json.dumps(all_data))
        compression_ratio = (1 - filtered_size / total_size) * 100
        
        print(f"  Original data: {total_size:,} chars")
        print(f"  Filtered data: {filtered_size:,} chars")
        print(f"  Compression: {compression_ratio:.1f}% reduction")
        print(f"  Data preview (first 300 chars):")
        print(f"  {filtered_data_json[:300]}...")
        
        # STEP 3: Would use reasoner here (full model with filtered data)
        print(f"\n[STEP 3] 💡 Reasoner: Would process with full model + filtered data")
        print(f"  ✓ Full model (llama-3.3-70b) gets only relevant context")
        print(f"  ✓ Reduced token usage = faster response + lower cost")
    
    print(f"\n{'=' * 70}")
    print("✅ Demo complete!")
    print("=" * 70)
    print("\nKey Benefits:")
    print("  • Call 1 (Router): ~500 tokens, <100ms (cheap model)")
    print("  • Call 2 (Reasoner): Only relevant data (efficient)")
    print("  • Total savings: ~80% token reduction vs single large call")


if __name__ == "__main__":
    asyncio.run(demo_routing_pattern())
