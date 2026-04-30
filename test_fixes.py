"""Quick test to verify fixes are working."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.intelligence.data_loader import load_all_data
from backend.intelligence.market_intelligence import MarketIntelligence


async def test_market_intelligence():
    """Test that market intelligence no longer throws AttributeError."""
    print("🧪 Testing Market Intelligence Fix...")
    print("=" * 60)
    
    try:
        data = load_all_data()
        market = MarketIntelligence()
        
        result = market.analyze_indices(data.get("market", {}))
        
        print(f"✅ Market analysis successful!")
        print(f"   Sentiment: {result.get('sentiment')}")
        print(f"   Top movers: {len(result.get('top_movers', []))} indices")
        print(f"\n✅ AttributeError fixed!")
        return True
        
    except AttributeError as e:
        print(f"❌ AttributeError still present: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_settings_security():
    """Test that API keys are not exposed in settings."""
    print("\n🔒 Testing Settings Security...")
    print("=" * 60)
    
    try:
        from backend.config import get_settings
        from backend.models.response_models import SafeSettingsResponse
        import json
        
        settings = get_settings()
        
        # Check that API keys are NOT in safe settings
        safe_response = SafeSettingsResponse(
            environment=settings.environment,
            api_base_url=settings.api_base_url,
            log_level=settings.log_level,
            database_configured=bool(settings.database_url)
        )
        
        response_dict = safe_response.model_dump()
        json_str = json.dumps(response_dict)
        
        # Verify no sensitive data
        sensitive_keywords = [
            "api_key", "groq_api_key", "langfuse", 
            "password", "secret", "credential"
        ]
        
        exposed = False
        for keyword in sensitive_keywords:
            if keyword.lower() in json_str.lower():
                print(f"❌ Found exposed sensitive data: {keyword}")
                exposed = True
        
        if not exposed:
            print(f"✅ No sensitive API keys in response!")
            print(f"   Safe response fields: {list(response_dict.keys())}")
            print(f"   Sample: {response_dict}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error testing settings security: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n" + "=" * 60)
    print("🚀 Verification Tests for Fixes")
    print("=" * 60 + "\n")
    
    test1 = await test_market_intelligence()
    test2 = await test_settings_security()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ All fixes verified successfully!")
    else:
        print("❌ Some issues remain")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
