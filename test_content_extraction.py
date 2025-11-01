#!/usr/bin/env python3
"""
Script de test pour vérifier l'extraction de contenu principal
"""

import asyncio
from services.valueserp_service import ValueSerpService

async def test_content_extraction():
    """Test l'extraction de contenu principal sur quelques URLs"""
    
    service = ValueSerpService()
    
    # URLs de test avec différents types de sites
    test_urls = [
        "https://www.wikipedia.org",
        "https://www.lemonde.fr",
        "https://stackoverflow.com",
    ]
    
    print("🧪 Test d'extraction de contenu principal")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\n🔍 Test: {url}")
        print("-" * 30)
        
        try:
            content_data = await service._fetch_page_content(url)
            
            print(f"📊 Résultats:")
            print(f"   - Nombre de mots: {content_data['word_count']}")
            print(f"   - Qualité: {content_data['content_quality']}")
            print(f"   - H1: {content_data['h1'][:100]}..." if content_data['h1'] else "   - H1: (vide)")
            print(f"   - Contenu (100 premiers caractères): {content_data['content'][:100]}...")
            print(f"   - Images: {content_data['images']}")
            print(f"   - Liens internes: {content_data['internal_links']}")
            print(f"   - Liens externes: {content_data['external_links']}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_content_extraction()) 