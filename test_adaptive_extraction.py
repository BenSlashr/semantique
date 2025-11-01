#!/usr/bin/env python3
"""
Script de test pour l'extraction adaptative de contenu
"""

import asyncio
from services.valueserp_service import ValueSerpService

async def test_adaptive_extraction():
    """Test l'extraction adaptative sur différents types de sites"""
    
    service = ValueSerpService()
    
    # URLs de test avec différents défis d'extraction
    test_urls = [
        ("https://fr.wikipedia.org/wiki/École_de_commerce", "Wikipedia - Structure complexe"),
        ("https://www.onisep.fr/formation/les-principaux-domaines-de-formation/les-ecoles-de-commerce", "Onisep - Site institutionnel"),
        ("https://www.letudiant.fr/etudes/ecole-de-commerce.html", "L'Étudiant - Site média"),
        ("https://diplomeo.com/etablissements-ecoles_de_commerce", "Diplomeo - Plateforme éducative"),
        ("https://www.iscparis.com/", "ISC Paris - Site d'école"),
    ]
    
    print("🧪 Test d'extraction adaptative de contenu")
    print("=" * 60)
    
    for url, description in test_urls:
        print(f"\n📍 TEST: {description}")
        print(f"🔗 URL: {url}")
        print("-" * 40)
        
        try:
            # Test de l'extraction
            result = await service._fetch_page_content(url)
            
            word_count = result.get('word_count', 0)
            quality = result.get('content_quality', 'unknown')
            content_preview = result.get('content', '')[:200] + "..." if result.get('content') else "Aucun contenu"
            
            print(f"📊 Résultat:")
            print(f"   - Mots extraits: {word_count}")
            print(f"   - Qualité: {quality}")
            print(f"   - Aperçu: {content_preview}")
            
            # Analyse de la stratégie utilisée (basée sur les logs)
            if word_count > 1000:
                status = "✅ EXCELLENT"
            elif word_count > 300:
                status = "✅ BON"
            elif word_count > 100:
                status = "⚠️ ACCEPTABLE"
            elif word_count > 20:
                status = "⚠️ FAIBLE"
            else:
                status = "❌ ÉCHEC"
            
            print(f"   - Statut: {status}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    print(f"\n📈 RÉSUMÉ DU TEST:")
    print("L'extraction adaptative utilise 3 stratégies en cascade:")
    print("1. 🎯 Sélective: Cherche les sélecteurs de contenu principal (seuil: 100 mots)")
    print("2. 🧹 Exclusion: Supprime les éléments parasites du body (seuil: 50 mots)")
    print("3. 🚀 Agressive: Prend tout sauf scripts/styles (seuil: 20 mots)")

if __name__ == "__main__":
    asyncio.run(test_adaptive_extraction()) 